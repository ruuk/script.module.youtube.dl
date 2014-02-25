import urllib, sys
import xbmc

DEBUG = False

def LOG(text,debug=False):
	if debug and not DEBUG: return
	print 'script.module.youtube.dl: %s' % text

def ERROR(message):
	errtext = sys.exc_info()[1]
	print 'script.module.youtube.dl - %s::%s (%d) - %s' % (message, sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, errtext)
	if DEBUG:
		import traceback
		traceback.print_exc()
###############################################################################
# FIX: xbmcout instance in sys.stderr does not have isatty(), so we add it
###############################################################################
class replacement_stderr(sys.stderr.__class__):
	def isatty(self): return False
	
sys.stderr.__class__ = replacement_stderr
###############################################################################

try:
	import youtube_dl
except:
	ERROR('Failded to import youtube-dl')
	youtube_dl = None

###############################################################################
# FIXES: datetime.datetime.strptime evaluating as None?
###############################################################################
_utils_unified_strdate = youtube_dl.utils.unified_strdate
def _unified_strdate_wrap(date_str):
	try:
		return _utils_unified_strdate(date_str)
	except:
		return '00000000'
youtube_dl.utils.unified_strdate = _unified_strdate_wrap

import datetime		
_utils_date_from_str = youtube_dl.utils.date_from_str
def _date_from_str_wrap(date_str):
	try:
		return _utils_date_from_str(date_str)
	except:
		return datetime.datetime.now().date()
youtube_dl.utils.date_from_str = _date_from_str_wrap
###############################################################################

_YTDL = None
_DISABLE_DASH_VIDEO = True
_CALLBACK = None
_BLACKLIST = ['youtube:playlist', 'youtube:toplist', 'youtube:channel', 'youtube:user', 'youtube:search', 'youtube:show', 'youtube:favorites', 'youtube:truncated_url','vimeo:channel', 'vimeo:user', 'vimeo:album', 'vimeo:group', 'vimeo:review','dailymotion:playlist', 'dailymotion:user','generic']
_DEFAULT_USER_AGENT = 'Mozilla/5.0+(Windows+NT+6.2;+Win64;+x64;+rv:16.0.1)+Gecko/20121011+Firefox/16.0.1'

class VideoInfo():
	def __init__(self,ID=None):
		self.ID = ID
		self.title = ''
		self.description = ''
		self.thumbnail = ''
		self.webpage = ''
		self._streams = None
		self.sourceName = ''
		
	def streamURL(self):
		if self._streams: return self._streams[0]['url']
		return ''
	
	def streams(self):
		return self._streams
		
	def hasMultipleStreams(self):
		if not self._streams: return False
		if len(self._streams) > 1: return True
		return False

class YoutubeDLWrapper(youtube_dl.YoutubeDL):
	def showMessage(self, msg):
		global _CALLBACK
		if _CALLBACK:
			try:
				_CALLBACK(msg)
			except:
				ERROR('Error in callback. Removing.')
				
				_CALLBACK = None
		else:
			pass
			#print msg.encode('ascii','replace')
			
	def add_info_extractor(self, ie):
		if ie.IE_NAME in _BLACKLIST: return
		# Fix ##################################################################
		module = sys.modules.get(ie.__module__)
		if module:
			if hasattr(module,'unified_strdate'): module.unified_strdate = _unified_strdate_wrap
			if hasattr(module,'date_from_str'): module.date_from_str = _date_from_str_wrap
		########################################################################
		youtube_dl.YoutubeDL.add_info_extractor(self,ie)

	def to_stdout(self, message, skip_eol=False, check_quiet=False):
		"""Print message to stdout if not in quiet mode."""
		if self.params.get('logger'):
			self.params['logger'].debug(message)
		elif not check_quiet or not self.params.get('quiet', False):
			message = self._bidi_workaround(message)
			terminator = ['\n', ''][skip_eol]
			output = message + terminator
			self.showMessage(output)

	def to_stderr(self, message):
		"""Print message to stderr."""
		assert type(message) == type('')
		if self.params.get('logger'):
			self.params['logger'].error(message)
		else:
			message = self._bidi_workaround(message)
			output = message + '\n'
			self.showMessage(output)
												
	def report_warning(self, message):
		#overidden to get around error on missing stderr.isatty attribute
		_msg_header = 'WARNING:'
		warning_message = '%s %s' % (_msg_header, message)
		self.to_stderr(warning_message)
		
	def report_error(self, message, tb=None):
		#overidden to get around error on missing stderr.isatty attribute
		_msg_header = 'ERROR:'
		error_message = '%s %s' % (_msg_header, message)
		self.trouble(error_message, tb)

###############################################################################
# Private Methods					
###############################################################################
def _getYTDL():
	global _YTDL
	if _YTDL: return _YTDL
	if DEBUG:
		_YTDL = YoutubeDLWrapper({'verbose':True})
	else:
		_YTDL = YoutubeDLWrapper()
	_YTDL.add_default_info_extractors()
	return _YTDL
	
def _selectVideoQuality(r,quality=1):
		if 'entries' in r and not 'formats' in r:
			entries = r['entries']
		elif 'formats' in r and r['formats']:
			entries = [r]
		elif 'url' in r:
			return [{'url':r['url'],'title':r.get('title',''),'thumbnail':r.get('thumbnail','')}]
		minHeight = 0
		maxHeight = 480
		if quality > 1:
			minHeight = 721
			maxHeight = 1080
		elif quality > 0:
			minHeight = 481
			maxHeight = 720
		LOG('Quality: {0}'.format(quality),debug=True)
		urls = []
		for entry in entries:
			defFormat = None
			defMax = 0
			defPref = -1000
			prefFormat = None
			prefMax = 0
			prefPref = -1000
			index = {}
			formats = entry['formats']
			for i in range(0,len(formats)): index[formats[i]['format_id']] = i
			keys = sorted(index.keys())
			fallback = formats[index[keys[0]]]
			for fmt in keys:
				fdata = formats[index[fmt]]
				if not 'height' in fdata: continue
				if _DISABLE_DASH_VIDEO and 'dash' in fdata.get('format_note','').lower(): continue
				h = fdata['height']
				p = fdata.get('preference',1)
				if h >= minHeight and h <= maxHeight:
					if (h >= prefMax and p > prefPref) or (h > prefMax and p >= prefPref):
						prefMax = h
						prefPref = p
						prefFormat = fdata
				elif(h >= defMax and h <= maxHeight and p > defPref) or (h > defMax and h <= maxHeight and p >= defPref):
						defMax = h
						defFormat = fdata
						defPref = p
			if prefFormat:
				LOG('[{3}] Using Preferred Format: {0} ({1}x{2})'.format(prefFormat['format'],prefFormat.get('width','?'),prefMax,entry.get('title','').encode('ascii','replace')),debug=True)
				url = prefFormat['url']
			elif defFormat:
				LOG('[{3}] Using Default Format: {0} ({1}x{2})'.format(defFormat['format'],defFormat.get('width','?'),defMax,entry.get('title','').encode('ascii','replace')),debug=True)
				url = defFormat['url']
			else:
				LOG('[{3}] Using Fallback Format: {0} ({1}x{2})'.format(fallback['format'],fallback.get('width','?'),fallback.get('height','?'),entry.get('title','').encode('ascii','replace')),debug=True)
				url = fallback['url']
			if url.find("rtmp") == -1:
				url += '|' + urllib.urlencode({'User-Agent':entry.get('user_agent') or _DEFAULT_USER_AGENT})
			else:
				url += ' playpath='+fdata['play_path']
			urls.append({'url':url,'title':entry.get('title',''),'thumbnail':entry.get('thumbnail','')})
		return urls
		
def _getYoutubeDLVideo(url,quality=1):
	ytdl = _getYTDL()
	r = ytdl.extract_info(url,download=False)
	urls =  _selectVideoQuality(r, quality)
	if not urls: return None
	info = VideoInfo(r.get('id',''))
	info._streams = urls
	info.title = r.get('title',urls[0]['title'])
	info.description = r.get('description','')
	info.thumbnail = r.get('thumbnail',urls[0]['thumbnail'])
	return info

###############################################################################
# Public Methods					
###############################################################################
def setOutputCallback(callback):
	global _CALLBACK
	_CALLBACK = callback
	
def getVideoInfo(url,quality=1):
	try:
		info = _getYoutubeDLVideo(url,quality)
		if not info: return None
	except:
		ERROR('_getYoutubeDLVideo() failed')
		return None
	return info

	
def mightHaveVideo(url):
	ytdl = _getYTDL()
	for ies in ytdl._ies:
		if ies.suitable(url):
			return True
	return False
	
def disableDASHVideo(disable):
	global _DISABLE_DASH_VIDEO
	_DISABLE_DASH_VIDEO = disable

###############################################################################
# xbmc player functions					
###############################################################################
def play(path,preview=False):
	xbmc.executebuiltin('PlayMedia(%s,,%s)' % (path,preview and 1 or 0))
	
def pause():
	if isPlaying(): control('play')
	
def resume():
	if not isPlaying(): control('play')
	
def current():
	return xbmc.getInfoLabel('Player.Filenameandpath')

def control(command):
	xbmc.executebuiltin('PlayerControl(%s)' % command)

def isPlaying():
		return xbmc.getCondVisibility('Player.Playing') and xbmc.getCondVisibility('Player.HasVideo')
	
def playAt(path,h=0,m=0,s=0,ms=0):
	xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.Open", "params": {"item":{"file":"%s"},"options":{"resume":{"hours":%s,"minutes":%s,"seconds":%s,"milliseconds":%s}}}, "id": 1}' % (path,h,m,s,ms)) #@UnusedVariable
