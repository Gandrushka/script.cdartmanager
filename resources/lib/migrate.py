import os
import xbmc
import xbmcvfs
import xbmcaddon
import settings

from sqlite3 import dbapi2 as sqlite3

__settings__ = settings.Settings()

LEGACY_ADDON_ID = 'script.cdartmanager'
LEGACY_DB_FILE = 'l_cdart.db'
LEGACY_STATUS_FILE = '.legacy_data_migrated'


# @TODO: import once or use as mbid source?
class LegacyDB:

    def __init__(self):

        self.legacy_db = None
        # legacy addon still installed?
        settings.log("Migration: checking, you can safely ignore 'Unknown addon' errors...")
        try:
            self.legacy_db = xbmc.translatePath(os.path.join(xbmcaddon.Addon(id=LEGACY_ADDON_ID).getAddonInfo("profile"), LEGACY_DB_FILE))
        except RuntimeError:
            pass

        try:
            self.legacy_db = xbmc.translatePath(os.path.join(__settings__.getProfile(), os.pardir, LEGACY_ADDON_ID, LEGACY_DB_FILE))
        except RuntimeError:
            pass

        if self.legacy_db is None or not xbmcvfs.exists(self.legacy_db):
            self.legacy_db = None
            settings.log("Migration: LegacyDB not found.")
        else:
            settings.log("Migration: LegacyDB found.")

    def get_db(self):
        return self.legacy_db

    def get_artists(self):
        if self.get_db():
            result = []
            conn = None
            try:
                conn = sqlite3.connect(self.get_db())
                c = conn.cursor()
                c.execute("select distinct name, musicbrainz_artistid from lalist union select distinct name, musicbrainz_artistid from local_artists order by name")
                data = c.fetchall()
                c.close()
                for item in data:
                    result.append({"artist": item[0], "artist_mbid": item[1]})
            except RuntimeError as e:
                settings.log(e, xbmc.LOGWARNING)
            finally:
                if conn is not None:
                    conn.close()
            return result
        else:
            return None

    def get_albums(self):
        if self.get_db():
            result = []
            conn = None
            try:
                conn = sqlite3.connect(self.get_db())
                c = conn.cursor()
                c.execute("select distinct artist, musicbrainz_artistid, title, musicbrainz_albumid from alblist")
                data = c.fetchall()
                c.close()
                for item in data:
                    result.append({"artist": item[0], "artist_mbid": item[1], "album": item[2], "album_mbid": item[3]})
            except RuntimeError as e:
                settings.log(e, xbmc.LOGWARNING)
            finally:
                if conn is not None:
                    conn.close()
            return result
        else:
            return None


# def is_migrated(set_=False):
#     if set_:
#         try:
#             status_file = os.path.join(__settings__.getDataStoreBaseDir(), LEGACY_STATUS_FILE)
#             f = xbmcvfs.File(status_file, 'w')
#             f.close()
#             return True
#         except IOError:
#             return False
#     else:
#         return xbmcvfs.exists(os.path.join(__settings__.getDataStoreBaseDir(), LEGACY_STATUS_FILE))
