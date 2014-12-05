# -*- coding: utf-8 -*-
import sys, json, binascii
import xbmc
from lib import YDStreamExtractor
from lib.yd_private_libs import util, servicecontrol, jsonqueue
import threading

class Service(xbmc.Monitor):
    def __init__(self):
        self.downloadCount = 0
        self.controller = servicecontrol.ServiceControl()
        self.start()

    def onNotification(self, sender, method, data):
        if not sender == 'script.module.youtube.dl': return
        self.processCommand(method.split('.',1)[-1],self.controller.processCommandData(data)) #Remove the "Other." prefix

    def processCommand(self,command,args):
        if command == 'DOWNLOAD_STOP':
            YDStreamExtractor.cancelDownload()

    def queueDownload(self):
        try:
            data = sys.argv[-1]
            jsonqueue.XBMCJsonRAFifoQueue(util.QUEUE_FILE).push(data)
        except:
            util.ERROR('Could not get passed data')

    def getNextQueuedDownload(self):
        try:
            dataHEX = jsonqueue.XBMCJsonRAFifoQueue(util.QUEUE_FILE).pop()
            if not dataHEX: return None
            dataJSON = binascii.unhexlify(dataHEX)
            self.downloadCount+=1
            util.LOG('Loading from queue. #{0} this session'.format(self.downloadCount))
            return json.loads(dataJSON)
        except:
            import traceback
            traceback.print_exc()

        return None

    def start(self):
        self.queueDownload()

        if self.controller.status == 'ACTIVE': return

        try:
            self.controller.status = 'ACTIVE'
            self._start()
        finally:
            self.controller.status = ''

    def _start(self):
        util.LOG('DOWNLOAD SERVICE: START')
        info = self.getNextQueuedDownload()

        while info and not xbmc.abortRequested:
            t = threading.Thread(target=YDStreamExtractor._handleDownload,args=(info['path'],info['data'],True))
            t.start()

            while t.isAlive() and not xbmc.abortRequested:
                xbmc.sleep(100)

            info = self.getNextQueuedDownload()

        util.LOG('DOWNLOAD SERVICE: FINISHED')

Service()