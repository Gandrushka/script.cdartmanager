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

    def __init__(self, callback=None):

        self.__artists = None
        self.__albums = None

        self.__addon_artists = None
        self.__addon_albums = None

        self.update_datastore(None, callback)

    def update_datastore(self, retrieve_missing=None, callback=None):

        # auto migration
        auto_migrate = False
        is_artists_changed = False
        is_albums_changed = False

        self.__artists = kodi_rpc.get_artists(not(__settings__.getExpEnableAllArtits()))
        self.__albums = kodi_rpc.get_albums()

        if self.__addon_artists is None:
            self.__addon_artists = self.load_addon_dict(constants.DS_ARTISTS_FILE)
            auto_migrate = auto_migrate or len(self.__addon_artists) == 0
            for artist in self.__artists:
                artist_name = utils.smart_unicode(artist['artist'])
                if artist_name not in self.__addon_artists:
                    self.__addon_artists[artist_name] = {'mbid': utils.smart_unicode(artist['musicbrainzartistid'])}
                    is_artists_changed = True

        if self.__addon_albums is None:
            self.__addon_albums = self.load_addon_dict(constants.DS_ALBUMS_FILE)
            auto_migrate = auto_migrate or len(self.__addon_albums) == 0
            for album in self.__albums:
                artist_name = utils.smart_unicode(album['artist'][0])
                album_title = utils.smart_unicode(album['title'])
                if (artist_name, album_title) not in self.__addon_albums:
                    self.__addon_albums[(artist_name, album_title)] = {'mbid': utils.smart_unicode(album['musicbrainzalbumid'])}
                    is_albums_changed = True
                # we update our artists here too, if we find an albumartist with mbid for an artist without mbid...
                artist_mbid = utils.smart_unicode(album['musicbrainzalbumartistid'])
                if artist_name not in self.__addon_artists:  # artist not found
                    self.__addon_artists[artist_name] = {'mbid': artist_mbid}
                    is_artists_changed = True
                if not utils.is_mbid(self.__addon_artists[artist_name]['mbid']) and utils.is_mbid(artist_mbid):  # present but empty mbid
                    self.__addon_artists[artist_name]["mbid"] = artist_mbid
                    is_artists_changed = True

        if auto_migrate:
            legacy_db = migrate.LegacyDB()
            if legacy_db.get_db() is not None:

                legacy_artists = legacy_db.get_artists()
                for legacy_artist in legacy_artists:
                    legacy_artist_name = legacy_artist["artist"]
                    legacy_artist_mbid = legacy_artist["artist_mbid"]
                    if legacy_artist_name in self.__addon_artists:
                        self.__addon_artists[legacy_artist_name]["mbid"] = legacy_artist_mbid
                        is_artists_changed = True

                legacy_albums = legacy_db.get_albums()
                for legacy_album in legacy_albums:
                    legacy_artist_name = legacy_album["artist"]
                    legacy_artist_mbid = legacy_album["artist_mbid"]
                    legacy_album_key = (legacy_artist_name, legacy_album["album"])
                    legacy_album_mbid = legacy_album["album_mbid"]
                    if legacy_album_key in self.__addon_albums:
                        self.__addon_albums[legacy_album_key]["mbid"] = legacy_album_mbid
                        is_albums_changed = True
                    if legacy_artist_name not in self.__addon_artists:  # artist not found
                        self.__addon_artists[legacy_artist_name] = {'mbid': legacy_artist_mbid}
                        is_artists_changed = True
                    if not utils.is_mbid(self.__addon_artists[legacy_artist_name]['mbid']) and utils.is_mbid(legacy_artist_mbid):  # present but empty mbid
                        self.__addon_artists[legacy_artist_name]["mbid"] = legacy_artist_mbid
                        is_artists_changed = True

        canceled = False

        # we check albums first, as the response usually delivers an artist_id
        if not canceled:
            albums_len = self.albums_count()
            check_albums_online = retrieve_missing in ("albums", "all")
            for index, album_entry in enumerate(self.__albums):
                if 'artist' in album_entry and len(album_entry['artist']) > 0:
                    album_artist = album_entry['artist'][0]
                    album_title = album_entry['title']
                    if callback is not None:
                        canceled = callback(index, albums_len, album_artist, album_title)
                        if canceled:
                            break
                    self._complement_album_mbid(album_entry, check_albums_online)
            # @TODO: save file
            self.save_addon_dict(constants.DS_ALBUMS_FILE, self.__addon_albums)

        if not canceled:
            artist_len = self.artists_count()
            check_artists_online = retrieve_missing in ("artists", "all")
            for index, artist_entry in enumerate(self.__artists):
                artist_name = artist_entry['artist']
                if callback is not None:
                    canceled = callback(index, artist_len, artist_name)
                    if canceled:
                        break
                self._complement_artist_mbid(artist_entry, check_artists_online)
            # @TODO: save file
            self.save_addon_dict(constants.DS_ARTISTS_FILE, self.__addon_artists)

        if canceled:
            #  @TODO clean up (and exit script?)
            pass

        # settings.log(self.__artists)
        # settings.log(self.__albums)
        # settings.log("Artists w/o mbid: %s" % self.get_artist_count_no_mbid())
        # settings.log("Albums w/o mbid: %s" % self.get_album_count_no_mbid())

    def _complement_artist_mbid(self, artist_entry, online=False):
        artist_name = utils.smart_unicode(artist_entry['artist'])

        # @TODO: check if addon artists is none

        artist_entry['mbid'] = None
        if artist_name in self.__addon_artists and utils.is_mbid(self.__addon_artists[artist_name]['mbid']):
            artist_entry['mbid'] = self.__addon_artists[artist_name]['mbid']  # get from datastore
        else:
            # otherwise check the alternative sources (and store it)
            if "musicbrainzartistid" in artist_entry and artist_entry['musicbrainzartistid'] != "":
                mbid = artist_entry['musicbrainzartistid']
                if utils.is_mbid(mbid):
                    artist_entry['mbid'] = mbid
                    self.__addon_artists[artist_name]['mbid'] = mbid
                    # @TODO save file
            elif online:
                mbid = mbid_finder.MBIDFinder(artist_entry['artist']).find()
                if utils.is_mbid(mbid.artist):
                    artist_entry['mbid'] = mbid.artist
                    self.__addon_artists[artist_name]['mbid'] = mbid.artist
                    # @TODO save file

    def _complement_album_mbid(self, album_entry, online=False):

        album_artist = utils.smart_unicode(album_entry['artist'][0])
        album_name = utils.smart_unicode(album_entry['title'])
        album_key = (album_artist, album_name)

        album_entry['mbid'] = None
        if album_key in self.__addon_albums and utils.is_mbid(self.__addon_albums[album_key]['mbid']):
            album_entry['mbid'] = self.__addon_albums[album_key]['mbid']  # get from datastore
        else:
            # otherwise check the alternative sources (and store it)
            if "musicbrainzalbumid" in album_entry and album_entry['musicbrainzalbumid'] != "":
                mbid = album_entry['musicbrainzalbumid']
                if utils.is_mbid(mbid):
                    album_entry['mbid'] = mbid
                    self.__addon_albums[album_key]['mbid'] = mbid
                    # @TODO save file
            elif online:
                # musicbrainz_albuminfo, discard = xxx_musicbrainz.get_musicbrainz_album(album_title, album_artist, 0, 1)
                mbid_result = mbid_finder.MBIDFinder(album_artist, album_name).find()
                if mbid_result.has_album:
                        album_entry['mbid'] = mbid_result.album
                        self.__addon_albums[album_key]['mbid'] = mbid_result.album
                if mbid_result.has_artist:
                    artist_entry = self.artists_find_artist(album_artist)
                    if artist_entry is not None:
                        # we update the artist here if present, this saves an API call to find the artist by name later
                        artist_entry['mbid'] = mbid_result.artist
                        self.__addon_artists[album_artist]['mbid'] = mbid_result.artist
                        # @TODO save file

    def artists_find_artist(self, artist_name):
        artist = utils.smart_unicode(artist_name)
        return next((item for item in self.__artists if utils.smart_unicode(item["artist"]) == artist), None)

    def artists_count(self):
        return len(self.__artists)

    def artists_count_no_mbid(self):
        return len([item for item in self.__artists if item["mbid"] is None])

    def albums_find(self, album_artist_name, album_title):
        artist = utils.smart_unicode(album_artist_name)
        album = utils.smart_unicode(album_title)
        return next((item for item in self.__albums if utils.smart_unicode(item["artist"]) == artist and utils.smart_unicode(item["album"]) == album), None)

    def albums_count(self):
        return len(self.__albums)

    def albums_count_no_mbid(self):
        return len([item for item in self.__albums if item["mbid"] is None])

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
        settings.log(result)
        return result

    @staticmethod
    def save_addon_dict(ds_file_name, data):
        result = False
        file_name = __settings__.getDataStoreFile(ds_file_name)

        data_list = []
        if data is not None:
            for k, v in data.items():
                data_list.append({"k": k, "v": v})

        try:
            f = xbmcvfs.File(file_name, 'w')
            json.dump(data_list, f, indent=2)
            f.close()
            result = True
        except IOError:
            pass

        return result


class AddonData:

    def __init__(self, initial_dict=None):

        if initial_dict is None:
            self.__dict = {}
        else:
            self.__dict = initial_dict

        self.__is_changed = False

    def set_dict_value(self, key, valuekey, value):
        if key not in self.__dict:
            self.__dict[key] = {}
            self.__dict[key][valuekey] = value
            self.__is_changed = True
            return

        if valuekey not in self.__dict[key] or self.__dict[key][valuekey] != value:
            self.__dict[key][valuekey] = value
            self.__is_changed = True
            return

    def get_dict_value(self, key, valuekey):

        if key not in self.__dict and valuekey in self.__dict[key]:
            return self.__dict[key][valuekey]
        else:
            return None

    @property
    def is_changed(self):
        return self.__is_changed


class ArtistAddonData(AddonData):
    pass


class AlbumAddonData(AddonData):
    pass
