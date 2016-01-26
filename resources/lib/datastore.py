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

        canceled = False

        if self.__artists is None:
            self.__artists = kodi_rpc.get_artists(not(__settings__.getExpEnableAllArtits()))
        if self.__albums is None:
            self.__albums = kodi_rpc.get_albums()

        self.__addon_albums = self.load_addon_dict(constants.DS_ALBUMS_FILE)
        self.__addon_artists = self.load_addon_dict(constants.DS_ARTISTS_FILE)

        # on first run we migrate data from the legacy db...
        if self.artists_count() == 0 and self.albums_count() == 0:
            self.__legacy_db = migrate.LegacyDB()

        check_albums_online = retrieve_missing in ("albums", "all")
        albums_len = self.albums_count()
        index = 0
        for albumid, album in self.__albums.iteritems():
            if 'albumid' in album:
                if album['albumid'] not in self.__addon_albums:
                    self.__addon_albums[album['albumid']] = {}

                if callback is not None:
                    canceled = callback(index, albums_len, album['artist'][0], album['title'])
                    if canceled:
                        break

                self._complement_album(album, self.__addon_albums[album['albumid']], check_albums_online)

            index += 1

        check_artists_online = retrieve_missing in ("artists", "all")
        artists_len = self.artists_count()
        index = 0
        for artistid, artist in self.__artists.iteritems():

            if 'artistid' in artist:
                if artist['artistid'] not in self.__addon_artists:
                    self.__addon_artists[artist['artistid']] = {}

                if callback is not None:
                    canceled = callback(index, artists_len, artist['artist'])
                    if canceled:
                        break

                self._complement_artist(artist, self.__addon_artists[artist['artistid']], check_artists_online)

            index += 1

        if canceled:
            pass

        self.save_addon_dict(constants.DS_ALBUMS_FILE, self.__addon_albums)
        self.save_addon_dict(constants.DS_ARTISTS_FILE, self.__addon_artists)

        settings.log(self.__artists)
        settings.log(self.__addon_artists)

        settings.log(self.__albums)
        settings.log(self.__addon_albums)

        # settings.log("Artists w/o mbid: %s" % self.get_artist_count_no_mbid())
        # settings.log("Albums w/o mbid: %s" % self.get_album_count_no_mbid())

    def _complement_artist(self, kodi_entry, addon_entry, online=False):
        result = False
        if kodi_entry is not None and 'artist' in kodi_entry:
            artist = kodi_entry['artist']
            addon_entry['artist'] = artist

            if self.__legacy_db is not None:
                legacy_mbid = utils.extract_mbid(self.__legacy_db.artists, kodi_entry['artistid'])
                if legacy_mbid is not None:
                    addon_entry['mbid'] = legacy_mbid
                    addon_entry['mbid_source'] = self.SOURCE_LEGACY

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
                    result = True
            addon_entry['mbid'] = mbid

            if mbid is not None:
                kodi_entry['musicbrainzartistid'] = mbid

        return result  # True if updated online

    def _complement_album(self, kodi_entry, addon_entry, online=False):
        result = False
        if kodi_entry is not None and 'title' in kodi_entry:
            artist = kodi_entry['artist'][0]
            album = kodi_entry['title']
            addon_entry['artist'] = artist
            addon_entry['title'] = album

            addon_entry['paths'] = kodi_rpc.get_albumpaths(kodi_entry['albumid'])
            kodi_entry[u'paths'] = addon_entry['paths']

            if self.__legacy_db is not None:
                legacy_mbid = utils.extract_mbid(self.__legacy_db.albums, kodi_entry['albumid'])
                if legacy_mbid is not None:
                    addon_entry['mbid'] = legacy_mbid
                    addon_entry['mbid_source'] = self.SOURCE_LEGACY

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
                    result = True
                    # if we have a new album hit we also update the artist
                    artist_id = kodi_entry['artistid'][0]
                    artist_mbid = utils.extract_mbid(mbid_result.artist)
                    if artist_mbid is not None and artist_id is not None and artist_id in self.__addon_artists:
                        addon_artist = self.__addon_artists[artist_id]
                        if utils.extract_mbid(addon_artist, 'musicbrainzartistid') is None:
                            settings.log("Collateral artist update: %s (%s) / %s" % (artist, artist_id, artist_mbid))
                            addon_artist['mbid'] = artist_mbid
                            addon_artist['mbid_source'] = "%s (collateral)" % mbid_result.source

            addon_entry['mbid'] = mbid

            if mbid is not None:
                kodi_entry['musicbrainzalbumid'] = mbid

        return result  # True if updated online

    def artists_count(self):
        return len(self.__artists)

    def artists_count_no_mbid(self):
        if self.__artists is not None:
            return len([item for item in self.__artists.itervalues() if not utils.is_mbid(item["musicbrainzartistid"])])
        else:
            return 0

    def albums_count(self):
        return len(self.__albums)

    def albums_count_no_mbid(self):
        if self.__albums is not None:
            return len([item for item in self.__albums.itervalues() if not utils.is_mbid(item["musicbrainzalbumid"])])
        else:
            return 0

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
