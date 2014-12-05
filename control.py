# -*- coding: utf-8 -*-
import sys
from lib.yd_private_libs import util, servicecontrol, updater
import xbmcgui

class main():
    def __init__(self):
        arg = self.getArg()
        if arg == 'INFO':
            self.showInfo()
        elif arg == 'UPDATE':
            self.update()
        else:
            self.showOptions()

    def getArg(self):
        return sys.argv[-1]

    def showOptions(self):
        option = True
        while option:
            d = util.xbmcDialogSelect('Options')
            if servicecontrol.ServiceControl().isDownloading():
                d.addItem('stop','Stop Current Download')
                d.addItem('stop_all','Stop All Downloads')
                d.addItem('manage','Manage Queue')
            d.addItem('settings','Settings')

            option = d.getResult()
            if not option: return
            if option == 'stop':
                self.stopDownload()
            elif option == 'stop_all':
                self.stopAllDownloads()
            elif option == 'manage':
                self.manageQueue()
            elif option == 'settings':
                self.settings()

    def stopDownload(self):
        yes = xbmcgui.Dialog().yesno('Cancel Download','Cancel current download?')
        if yes: servicecontrol.ServiceControl().stopDownload()

    def stopAllDownloads(self):
        yes = xbmcgui.Dialog().yesno('Cancel Downloads','Cancel current download and','all queued downloads?')
        if yes: servicecontrol.ServiceControl().stopAllDownloads()

    def manageQueue(self):
        servicecontrol.ServiceControl().manageQueue()

    def settings(self):
        util.ADDON.openSettings()

    def update(self):
        updated = self._update()
        if updated:
            self.showInfo(updated=True)
        else:
            xbmcgui.Dialog().ok('Up To Date','youtube-dl core is already up to date!')

    @util.busyDialog
    def _update(self):
        return updater.updateCore(force=True)

    def showInfo(self,updated=False):
        updater.set_youtube_dl_importPath()
        import youtube_dl
        from lib import YDStreamUtils
        import time
        version = youtube_dl.version.__version__
        line1 = '{0} core version: [B]{1}[/B]'.format(updated and 'Updated' or 'Used', version)
        check = util.getSetting('last_core_check',0)
        line2 = 'Never checked for new version.'
        if check:
            duration = YDStreamUtils.durationToShortText(int(time.time() - check))
            line2 = 'Last check for new version: [B]{0}[/B] ago'.format(duration)

        xbmcgui.Dialog().ok('Info',line1,'',line2)

main()

