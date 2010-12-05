__scriptname__    = "CDArt Manager Script"
__scriptID__      = "script.cdartmanager"
__author__        = "Giftie"
__version__       = "1.1.9"
__credits__       = "Ppic, Reaven, Imaginos, redje, Jair, "
__credits2__      = "Chaos_666, Magnatism"
__XBMC_Revision__ = "35415"
__date__          = "12-04-10"
import sys
import os
import xbmcaddon
import xbmc
from pysqlite2 import dbapi2 as sqlite3

__settings__ = xbmcaddon.Addon(__scriptID__)
__language__ = __settings__.getLocalizedString

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __settings__.getAddonInfo('path'), 'resources' ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "skins", "Default" ) )

sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ))

print BASE_RESOURCE_PATH


addon_work_folder = os.path.join(xbmc.translatePath( "special://profile/addon_data/" ), __scriptID__)
addon_db = os.path.join(addon_work_folder, "l_cdart.db")
settings_file = os.path.join(addon_work_folder, "settings.xml")

if ( __name__ == "__main__" ):
    print "############################################################"
    print "#    %-50s    #" % __scriptname__
    print "#        default.py module                                 #"
    print "#    %-50s    #" % __scriptID__
    print "#    %-50s    #" % __author__
    print "#    %-50s    #" % __version__
    print "#    %-50s    #" % __credits__
    print "#    Thanks the the help guys...                           #"
    print "############################################################"
    query = "SELECT version FROM counts"
    try:
        conn_l = sqlite3.connect(addon_db)
        c = conn_l.cursor()
        c.execute(query)
        version=c.fetchall()
        for item in version:
            if item[0]=="1.1.8":
                print item[0]
            else:
                os.remove(addon_db)
                os.remove(settings_file)
                __settings__.openSettings()
        c.close    
    except:
        os.remove(addon_db)
        os.remove(settings_file)
        __settings__.openSettings()
    path = __settings__.getAddonInfo('path')
    if not os.path.exists(addon_work_folder):
        __settings__.openSettings()
    import gui
    ui = gui.GUI( "script-cdartmanager.xml" , __settings__.getAddonInfo('path'), "Default")
    ui.doModal()
    del ui
    sys.modules.clear()
