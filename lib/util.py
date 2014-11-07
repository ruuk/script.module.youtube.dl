# -*- coding: utf-8 -*-
import xbmc

def busyDialog(func):
    def inner(*args,**kwargs):
        try:
            xbmc.executebuiltin("ActivateWindow(10138)")
            return func(*args,**kwargs)
        finally:
            xbmc.executebuiltin("Dialog.Close(10138)")
    return inner