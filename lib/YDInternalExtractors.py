import re
from youtube_dl.extractor.common import InfoExtractor

class RTMPIE(InfoExtractor):
    _VALID_URL = r'(?i)rtmp://(?P<host>[^\/]+)/(?P<app>[^\/]+)/(?P<play_path>[^\/]+)/?'
    IE_DESC = 'RTMP Stream URL Handler'

    _TEST = {
        'url': 'http://test.com/url',
        'info_dict': {
            'id': '0',
            'title': 'Test RTMP Stream',
            'description': 'Test',
        }
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)

        formats = [
            {
                'url': url,
                'format_id': '0',
                'app': m.group('app'),
                'play_path': m.group('play_path'),
                #'player_url': 'http://www.cbsnews.com/[[IMPORT]]/vidtech.cbsinteractive.com/player/3_3_0/CBSI_PLAYER_HD.swf',
                'page_url': 'http://{0}'.format(m.group('host')),
                'duration':10,
                'is_live':True,
                'rtmp_live':True,
                'ext': 'flv',
            }
        ]

        return {
            'id': '0',
            'title': 'Unknown RTMP Stream',
            'formats': formats,
        }