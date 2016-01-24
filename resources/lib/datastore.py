import xbmcvfs
import utils
import kodi_rpc
import settings
import mbid_finder
import json
import constants
import migrate

__settings__ = settings.Settings()


class Datastore:

    SOURCE_KODI = 'Kodi'
    SOURCE_LEGACY = 'Legacy'

    def __init__(self, callback=None):

        self.__artists = None
        self.__albums = None

        self.__addon_artists = None
        self.__addon_albums = None

        self.__legacy_db = None

        self.update_datastore(None, callback)

    def update_datastore(self, retrieve_missing=None, callback=None):

        # auto migration
        auto_migrate = False

        if self.__artists is None:
            self.__artists = kodi_rpc.get_artists(not(__settings__.getExpEnableAllArtits()))
        if self.__albums is None:
            self.__albums = kodi_rpc.get_albums()

        self.__addon_albums = self.load_addon_dict(constants.DS_ALBUMS_FILE)
        self.__addon_artists = self.load_addon_dict(constants.DS_ARTISTS_FILE)

        dev_mode = __settings__.isDevMode()

        # on first run we migrate data fro mthe legacy db...
        first_run = self.artists_count() == 0 and self.albums_count() == 0

        check_artists_online = retrieve_missing in ("artists", "all")
        artists_len = self.artists_count()
        for index, artist in enumerate(self.__artists):

            if check_artists_online and dev_mode:
                check_artists_online = index < 20

            if 'artistid' in artist:
                if artist['artistid'] not in self.__addon_artists:
                    self.__addon_artists[artist['artistid']] = {}

                if callback is not None:
                    canceled = callback(index, artists_len, artist['artist'])
                    if canceled:
                        break

                self._complement_artist(artist, self.__addon_artists[artist['artistid']], check_artists_online)

        check_albums_online = retrieve_missing in ("albums", "all")
        albums_len = self.albums_count()
        for index, album in enumerate(self.__albums):

            if check_albums_online and dev_mode:
                check_albums_online = index < 20

            if 'albumid' in album:
                if album['albumid'] not in self.__addon_albums:
                    self.__addon_albums[album['albumid']] = {}

                self._complement_album(album, self.__addon_albums[album['albumid']], check_albums_online)

                if callback is not None:
                    canceled = callback(index, albums_len, album['artist'][0], album['title'])
                    if canceled:
                        break

            # auto_migrate = auto_migrate or len(self.__addon_artists) == 0
            # for artist in self.__artists:
            #     artist_name = utils.smart_unicode(artist['artist'])
            #     if artist_name not in self.__addon_artists:
            #         mbid = artist['musicbrainzartistid']
            #         self.__addon_artists[artist_name] = {'mbid': utils.smart_unicode(mbid)}
            #         if utils.is_mbid(mbid):
            #             self.__addon_artists[artist_name]['mbid_source'] = self.SOURCE_KODI

        # if self.__addon_albums is None:
        #     self.__addon_albums = self.load_addon_dict(constants.DS_ALBUMS_FILE)
        #     for album in self.__albums:
        #         if 'albumid' in album:
        #             if album['albumid'] not in self.__addon_albums:
        #                 self.__addon_albums[album['albumid']] = {}
        #             self._complement_album(album, self.__addon_albums[album['albumid']])

            # auto_migrate = auto_migrate or len(self.__addon_albums) == 0
            # for album in self.__albums:
            #     artist_name = utils.smart_unicode(album['artist'][0])
            #     album_title = utils.smart_unicode(album['title'])
            #
            #     if (artist_name, album_title) not in self.__addon_albums:
            #         mbid = album['musicbrainzalbumid']
            #         self.__addon_albums[(artist_name, album_title)] = {'mbid': utils.smart_unicode(mbid)}
            #         if utils.is_mbid(mbid):
            #             self.__addon_albums[(artist_name, album_title)]['mbid_source'] = self.SOURCE_KODI
            #
            #     # we update our artists here too, if we find an albumartist with mbid for an artist without mbid...
            #     artist_mbid = utils.smart_unicode(album['musicbrainzalbumartistid'])
            #     if artist_name not in self.__addon_artists:  # artist not found
            #         self.__addon_artists[artist_name] = {'mbid': artist_mbid}
            #         if utils.is_mbid(artist_mbid):
            #             self.__addon_artists[artist_name]['mbid_source'] = self.SOURCE_KODI
            #     if not utils.is_mbid(self.__addon_artists[artist_name]['mbid']) and utils.is_mbid(artist_mbid):  # present but invalid mbid
            #         self.__addon_artists[artist_name]["mbid"] = artist_mbid
            #         self.__addon_artists[artist_name]["mbid_source"] = self.SOURCE_KODI

        auto_migrate = False

        # if auto_migrate:
        #     legacy_db = migrate.LegacyDB()
        #     if legacy_db.get_db() is not None:
        #
        #         legacy_artists = legacy_db.get_artists()
        #         for legacy_artist in legacy_artists:
        #             legacy_artist_name = legacy_artist["artist"]
        #             legacy_artist_mbid = legacy_artist["artist_mbid"]
        #             if legacy_artist_name in self.__addon_artists:
        #                 self.__addon_artists[legacy_artist_name]["mbid"] = legacy_artist_mbid
        #                 self.__addon_artists[legacy_artist_name]["mbid_source"] = self.SOURCE_LEGACY
        #
        #         legacy_albums = legacy_db.get_albums()
        #         for legacy_album in legacy_albums:
        #             legacy_artist_name = legacy_album["artist"]
        #             legacy_artist_mbid = legacy_album["artist_mbid"]
        #             legacy_album_key = (legacy_artist_name, legacy_album["album"])
        #             legacy_album_mbid = legacy_album["album_mbid"]
        #             if legacy_album_key in self.__addon_albums:
        #                 self.__addon_albums[legacy_album_key]["mbid"] = legacy_album_mbid
        #                 self.__addon_albums[legacy_album_key]["mbid_source"] = self.SOURCE_LEGACY
        #             if legacy_artist_name not in self.__addon_artists:  # artist not found
        #                 self.__addon_artists[legacy_artist_name] = {'mbid': legacy_artist_mbid, 'mbid_source': self.SOURCE_LEGACY}
        #             if not utils.is_mbid(self.__addon_artists[legacy_artist_name]['mbid']) and utils.is_mbid(legacy_artist_mbid):  # present but empty mbid
        #                 self.__addon_artists[legacy_artist_name]["mbid"] = legacy_artist_mbid
        #                 self.__addon_artists[legacy_artist_name]["mbid_source"] = self.SOURCE_LEGACY

        canceled = False

        # we check albums first, as the response usually delivers an artist_id
        # if not canceled:
        #     albums_len = self.albums_count()
        #     check_albums_online = retrieve_missing in ("albums", "all")
        #     for index, album_entry in enumerate(self.__albums):
        #         if 'artist' in album_entry and len(album_entry['artist']) > 0:
        #             album_artist = album_entry['artist'][0]
        #             album_title = album_entry['title']
        #             if callback is not None:
        #                 canceled = callback(index, albums_len, album_artist, album_title)
        #                 if canceled:
        #                     break
        #             settings.log("ALBUM: %s" % album_entry)
        #             self._complement_album_mbid(album_entry, check_albums_online)
        #
        # if not canceled:
        #     artist_len = self.artists_count()
        #     check_artists_online = retrieve_missing in ("artists", "all")
        #     for index, artist_entry in enumerate(self.__artists):
        #         artist_name = artist_entry['artist']
        #         if callback is not None:
        #             canceled = callback(index, artist_len, artist_name)
        #             if canceled:
        #                 break
        #         settings.log("ARTISTS: %s" % artist_entry)
        #         self._complement_artist_mbid(artist_entry, check_artists_online)

        if canceled:
            pass

        self.save_addon_dict(constants.DS_ALBUMS_FILE, self.__addon_albums)
        self.save_addon_dict(constants.DS_ARTISTS_FILE, self.__addon_artists)

        settings.log(self.__artists)
        settings.log(self.__albums)
        # settings.log("Artists w/o mbid: %s" % self.get_artist_count_no_mbid())
        # settings.log("Albums w/o mbid: %s" % self.get_album_count_no_mbid())

    def _complement_artist(self, kodi_entry, addon_entry, online=False):
        if kodi_entry is not None and 'artist' in kodi_entry:
            artist = kodi_entry['artist']
            addon_entry['artist'] = artist

            mbid = utils.extract_mbid(addon_entry, 'mbid')
            if mbid is None:
                mbid = utils.extract_mbid(kodi_entry, 'musicbrainzartistid')
                if mbid is not None:
                    addon_entry['mbid_source'] = self.SOURCE_KODI
            if mbid is None and online:
                mbid_result = mbid_finder.MBIDFinder(artist).find()
                mbid = utils.extract_mbid(mbid_result.artist)
                if mbid is not None:
                    addon_entry['mbid_source'] = mbid_result.source
            addon_entry['mbid'] = mbid

            if mbid is not None:
                kodi_entry['musicbrainzartistid'] = mbid

    def _complement_album(self, kodi_entry, addon_entry, online=False):
        if kodi_entry is not None and 'title' in kodi_entry:
            artist = kodi_entry['artist'][0]
            album = kodi_entry['title']
            addon_entry['artist'] = artist
            addon_entry['title'] = album

            addon_entry['paths'] = kodi_rpc.get_albumpaths(kodi_entry['albumid'])
            kodi_entry['paths'] = addon_entry['paths']

            mbid = utils.extract_mbid(addon_entry, 'mbid')
            if mbid is None:
                mbid = utils.extract_mbid(kodi_entry, 'musicbrainzalbumid')
                if mbid is not None:
                    addon_entry['mbid_source'] = self.SOURCE_KODI
            if mbid is None and online:
                mbid_result = mbid_finder.MBIDFinder(artist, album).find()
                mbid = utils.extract_mbid(mbid_result.album)
                if mbid is not None:
                    addon_entry['mbid_source'] = mbid_result.source
            addon_entry['mbid'] = mbid

            if mbid is not None:
                kodi_entry['musicbrainzalbumid'] = mbid


    # def _complement_artist_mbid(self, artist_entry, online=False):
    #     artist_name = utils.smart_unicode(artist_entry['artist'])
    #     if "musicbrainzartistid" in artist_entry and artist_entry['musicbrainzartistid'] != "":
    #         mbid = artist_entry['musicbrainzartistid']
    #         if utils.is_mbid(mbid):
    #             artist_entry['mbid'] = mbid
    #             self.__addon_artists[artist_name]['mbid'] = mbid
    #     elif online:
    #         mbid = mbid_finder.MBIDFinder(artist_entry['artist']).find()
    #         if utils.is_mbid(mbid.artist):
    #             artist_entry['mbid'] = mbid.artist
    #             self.__addon_artists[artist_name]['mbid'] = mbid.artist
    #
    #
    # def _complement_album_mbid(self, album_entry, online=False):
    #
    #     album_artist = utils.smart_unicode(album_entry['artist'][0])
    #     album_name = utils.smart_unicode(album_entry['title'])
    #     album_key = (album_artist, album_name)
    #
    #     album_entry['mbid'] = None
    #     if album_key in self.__addon_albums and utils.is_mbid(self.__addon_albums[album_key]['mbid']):
    #         album_entry['mbid'] = self.__addon_albums[album_key]['mbid']  # get from datastore
    #     else:
    #         # otherwise check the alternative sources (and store it)
    #         if "musicbrainzalbumid" in album_entry and album_entry['musicbrainzalbumid'] != "":
    #             mbid = album_entry['musicbrainzalbumid']
    #             if utils.is_mbid(mbid):
    #                 album_entry['mbid'] = mbid
    #                 self.__addon_albums[album_key]['mbid'] = mbid
    #         elif online:
    #             # musicbrainz_albuminfo, discard = xxx_musicbrainz.get_musicbrainz_album(album_title, album_artist, 0, 1)
    #             mbid_result = mbid_finder.MBIDFinder(album_artist, album_name).find()
    #             if mbid_result.has_album:
    #                     album_entry['mbid'] = mbid_result.album
    #                     self.__addon_albums[album_key]['mbid'] = mbid_result.album
    #             if mbid_result.has_artist:
    #                 artist_entry = self.artists_find_artist(album_artist)
    #                 if artist_entry is not None:
    #                     # we update the artist here if present, this saves an API call to find the artist by name later
    #                     artist_entry['mbid'] = mbid_result.artist
    #                     self.__addon_artists[album_artist]['mbid'] = mbid_result.artist

    # def artists_find_artist(self, artist_name):
    #     artist = utils.smart_unicode(artist_name)
    #     return next((item for item in self.__artists if utils.smart_unicode(item["artist"]) == artist), None)

    def artists_count(self):
        return len(self.__artists)

    def artists_count_no_mbid(self):
        return len([item for item in self.__artists if not utils.is_mbid(item["musicbrainzartistid"])])

    # def albums_find(self, album_artist_name, album_title):
    #     artist = utils.smart_unicode(album_artist_name)
    #     album = utils.smart_unicode(album_title)
    #     return next((item for item in self.__albums if utils.smart_unicode(item["artist"]) == artist and utils.smart_unicode(item["album"]) == album), None)

    def albums_count(self):
        return len(self.__albums)

    def albums_count_no_mbid(self):
        return len([item for item in self.__albums if not utils.is_mbid(item["musicbrainzalbumid"])])

    @staticmethod
    def load_addon_dict(ds_file_name):
        result = {}
        file_name = __settings__.getDataStoreFile(ds_file_name)
        if xbmcvfs.exists(file_name):
            f = xbmcvfs.File(file_name)
            data_list = json.load(f)
            f.close()
            for item in data_list:
                key = item["k"]
                if isinstance(key, list):
                    key = tuple(key)
                result[key] = item["v"]
        return result

    @staticmethod
    def save_addon_dict(ds_file_name, data):
        result = False
        file_name = __settings__.getDataStoreFile(ds_file_name)

        dev_mode = __settings__.isDevMode()
        dev_content = ['paths', 'artist', 'title']

        data_list = []
        if data is not None:
            for k, v in data.items():
                if not dev_mode:
                    for r in dev_content:
                        v.pop(r, None)
                data_list.append({"k": k, "v": v})
        try:
            f = xbmcvfs.File(file_name, 'w')
            json.dump(data_list, f, indent=2)
            f.close()
            result = True
        except IOError:
            pass

        return result


# class AddonData:
#
#     def __init__(self, initial_dict=None):
#
#         if initial_dict is None:
#             self.__dict = {}
#         else:
#             self.__dict = initial_dict
#
#         self.__is_changed = False
#
#     def set_dict_value(self, key, valuekey, value):
#         if key not in self.__dict:
#             self.__dict[key] = {}
#             self.__dict[key][valuekey] = value
#             self.__is_changed = True
#             return
#
#         if valuekey not in self.__dict[key] or self.__dict[key][valuekey] != value:
#             self.__dict[key][valuekey] = value
#             self.__is_changed = True
#             return
#
#     def get_dict_value(self, key, valuekey):
#
#         if key not in self.__dict and valuekey in self.__dict[key]:
#             return self.__dict[key][valuekey]
#         else:
#             return None
#
#     @property
#     def is_changed(self):
#         return self.__is_changed
#
#
# class ArtistAddonData(AddonData):
#     pass
#
#
# class AlbumAddonData(AddonData):
#     pass
