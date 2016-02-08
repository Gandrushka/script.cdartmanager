import xbmc
import settings
__settings__ = settings.Settings()


def lng(id_):
    if 32000 <= id_ < 33000:
        return __settings__.getAddon().getLocalizedString(id_)
    else:
        return xbmc.getLocalizedString(id_)

# Language IDs
LID_DASHBOARD = 32500
LID_ALBUMS = 132
LID_ARTISTS = 133
LID_SETTINGS = 5
LID_EXIT = 13012

LID_START = 335
LID_WAIT = 20186
LID_CANCEL = 222

# Language Strings
LNG_DASHBOARD = lng(LID_DASHBOARD)
LNG_ALBUMS = lng(LID_ALBUMS)
LNG_ARTISTS = lng(LID_ARTISTS)
LNG_SETTINGS = lng(LID_SETTINGS)
LNG_EXIT = lng(LID_EXIT)

LNG_START = lng(LID_START)
LNG_WAIT = lng(LID_WAIT)
LNG_CANCEL = lng(LID_CANCEL)
