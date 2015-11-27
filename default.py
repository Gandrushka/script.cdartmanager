import xbmc
import xbmcgui

import resources.lib.gui as gui
import resources.lib.constants as constants
import resources.lib.settings as settings

__settings__ = settings.Settings()


def clear_skin_properties():
    xbmcgui.Window(10000).setProperty("cdart_manager_running", "False")
    xbmcgui.Window(10000).setProperty("cdart_manager_allartist", "False")


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
        settings.log("Addon Database:    %s" % __settings__.getDatabaseFile(), xbmc.LOGNOTICE)
        settings.log("Addon settings:    %s" % __settings__.getSettingsFile(), xbmc.LOGNOTICE)
        settings.log("All Artist mode:   %s" % str(__settings__.getExpEnableAllArtits()), xbmc.LOGNOTICE)

        __settings__.reload(True)
        __settings__.to_log()

        # check for another instance
        if xbmcgui.Window(10000).getProperty("cdart_manager_running") == "True":
            raise SystemExit("cdART Manager Already running, exiting...")
        else:
            xbmcgui.Window(10000).setProperty("cdart_manager_running", "True")

        if __settings__.getExpEnableAllArtits():
            xbmcgui.Window(10000).setProperty("cdart_manager_allartist", "True")
        else:
            xbmcgui.Window(10000).setProperty("cdart_manager_allartist", "False")

        xbmc.executebuiltin('Dialog.Close(all, true)')
        ui = gui.GUI("script-cdartmanager.xml", __settings__.getPath(), "Default")  # GUI("script-cdartmanager.xml", __addon__.getAddonInfo('path'), "Default")
        xbmc.sleep(500)
        ui.doModal()
        del ui

    except SystemExit as e:
        settings.log(e.message, xbmc.LOGERROR)

    except:
        raise

    finally:
        clear_skin_properties()
        settings.log("cdART Manager exited", xbmc.LOGNOTICE)
