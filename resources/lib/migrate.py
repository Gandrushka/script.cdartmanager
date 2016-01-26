# -*- coding: utf-8 -*-

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


class LegacyDB:

    def __init__(self):

        self.legacy_db = None
        # legacy addon still installed?
        settings.log("Migration: checking, you can safely ignore 'Unknown addon' errors...", xbmc.LOGWARNING)
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
            self.artists = self.__get_artists()
            self.albums = self.__get_albums()

    def __get_db(self):
        return self.legacy_db

    def __get_artists(self):
        if self.__get_db() is not None:
            result = {}
            conn = None
            try:
                conn = sqlite3.connect(self.__get_db())
                c = conn.cursor()
                c.execute("select distinct local_id, musicbrainz_artistid from lalist union select distinct local_id, musicbrainz_artistid from local_artists order by local_id")
                data = c.fetchall()
                c.close()
                for item in data:
                    result[item[0]] = item[1]
            except RuntimeError as e:
                settings.log(e, xbmc.LOGWARNING)
            finally:
                if conn is not None:
                    conn.close()
            return result
        else:
            return None

    def __get_albums(self):
        if self.__get_db() is not None:
            result = {}
            conn = None
            try:
                conn = sqlite3.connect(self.__get_db())
                c = conn.cursor()
                c.execute("select distinct album_id, musicbrainz_albumid from alblist")
                data = c.fetchall()
                c.close()
                for item in data:
                    result[item[0]] = item[1]
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
