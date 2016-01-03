import xbmc
import xbmcgui

import resources.lib.gui as gui
import resources.lib.constants as constants
import resources.lib.settings as settings

__settings__ = settings.Settings()


if __name__ == "__main__":

    try:

        xbmc.executebuiltin('Dialog.Close(all, true)')

        # log startup
        settings.log(constants.LOG_STARTUP_BORDER, xbmc.LOGNOTICE)
        settings.log(constants.LOG_STARTUP_LINE % (__settings__.getName() + " (" + __settings__.getId() + ")"), xbmc.LOGNOTICE)
        settings.log(constants.LOG_STARTUP_LINE % ("Branch " + constants.ADDON_BRANCH + ", Version " + __settings__.getVersion()), xbmc.LOGNOTICE)
        settings.log(constants.LOG_STARTUP_LINE % ("Provided by " + __settings__.getAuthor()), xbmc.LOGNOTICE)
        for l in constants.LOG_STARTUP_STATIC:
            settings.log(constants.LOG_STARTUP_LINE % l, xbmc.LOGNOTICE)
        settings.log(constants.LOG_STARTUP_BORDER, xbmc.LOGNOTICE)
        settings.log("Addon Work Folder: %s" % __settings__.getWorkBasePath(), xbmc.LOGNOTICE)
        settings.log("Addon settings:    %s" % __settings__.getSettingsFile(), xbmc.LOGNOTICE)
        # settings.log("All Artist mode:   %s" % str(__settings__.getExpEnableAllArtits()), xbmc.LOGNOTICE)

        __settings__.reload(True)
        __settings__.to_log()

        xbmc.executebuiltin('Dialog.Close(all, true)')
        ui = gui.GUI("script-cdartmanager.xml", __settings__.getPath(), constants.SKIN_FOLDER)
        xbmc.sleep(500)
        ui.doModal()
        settings.log("Closed, @TODO: save missing.txt if selected")
        del ui

    except SystemExit as e:
        settings.log(e.message, xbmc.LOGERROR)

    except:
        raise

    finally:
        settings.log("cdART Manager exited", xbmc.LOGNOTICE)
