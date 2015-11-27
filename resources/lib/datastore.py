import os
import xbmc
import xbmcvfs
import resources.lib.utils
import utils
import kodi_rpc
import settings
import mbid_finder

__settings__ = settings.Settings()


class Datastore:

    __artists = None
    __albums = None

    def __init__(self, callback=None):
        self.update_datastore(None, callback)

    def update_datastore(self, retrieve_missing=None, callback=None):

        if self.__artists is None:
            self.__artists = kodi_rpc.get_artists(__settings__.getExpEnableAllArtits())
        if self.__albums is None:
            self.__albums = kodi_rpc.get_albums()

        canceled = False

        # we check albums first, as the response delivers an artist_id
        if not canceled:
            albums_len = self.count_albums()
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

        if not canceled:
            artist_len = self.count_artists()
            check_artists_online = retrieve_missing in ("artists", "all")
            for index, artist_entry in enumerate(self.__artists):
                artist_name = artist_entry['artist']
                if callback is not None:
                    canceled = callback(index, artist_len, artist_name)
                    if canceled:
                        break
                self._complement_artist_mbid(artist_entry, check_artists_online)

        if canceled:
            #  @TODO clean up (and exit script?)
            pass

        # settings.log(self.__artists)
        # settings.log(self.__albums)
        # settings.log("Artists w/o mbid: %s" % self.get_artist_count_no_mbid())
        # settings.log("Albums w/o mbid: %s" % self.get_album_count_no_mbid())

    @staticmethod
    def _get_album_dsdir(artist_name, album_name):
        return __settings__.getDataStoreDir(resources.lib.utils.sanitize_fs(artist_name, True), resources.lib.utils.sanitize_fs(album_name, True))

    @staticmethod
    def _get_artist_dsdir(artist_name):
        return __settings__.getDataStoreDir(resources.lib.utils.sanitize_fs(artist_name, True))

    def _complement_artist_mbid(self, artist_entry, online=False):
        artist_mbid_path = MBIDPath(os.path.join(Datastore._get_artist_dsdir(artist_entry['artist'])))

        # first check if we have already stored a mbid
        artist_entry['mbid'] = artist_mbid_path.read_mbid_file()
        if artist_entry['mbid'] is not None:
            return
        else:
            # otherwise check the alternative sources (and store it)
            if "musicbrainzartistid" in artist_entry and artist_entry['musicbrainzartistid'] != "":
                mbid = artist_entry['musicbrainzartistid']
                if mbid_finder.MBIDResult.is_mbid(mbid):
                    artist_entry['mbid'] = mbid
                    artist_mbid_path.write_mbid_file(mbid)
            elif online:
                mbid = mbid_finder.MBIDFinder(artist_entry['artist']).find()
                if mbid_finder.MBIDResult.is_mbid(mbid.artist_mbid):
                    artist_entry['mbid'] = mbid.artist_mbid
                    artist_mbid_path.write_mbid_file(mbid.artist_mbid)

    def _complement_album_mbid(self, album_entry, online=False):
        album_artist = album_entry['artist'][0]
        album_title = album_entry['title']
        album_mbid_path = MBIDPath(os.path.join(Datastore._get_album_dsdir(album_artist, album_title)))

        album_entry['mbid'] = album_mbid_path.read_mbid_file()
        if album_entry['mbid'] is not None:
            return
        else:
            # otherwise check the alternative sources (and store it)
            if "musicbrainzalbumid" in album_entry and album_entry['musicbrainzalbumid'] != "":
                mbid = album_entry['musicbrainzalbumid']
                if mbid_finder.MBIDResult.is_mbid(mbid):
                    album_entry['mbid'] = mbid
                    album_mbid_path.write_mbid_file(mbid)
            elif online:
                # musicbrainz_albuminfo, discard = xxx_musicbrainz.get_musicbrainz_album(album_title, album_artist, 0, 1)
                mbid_result = mbid_finder.MBIDFinder(album_artist, album_title).find()
                if mbid_result.has_album_mbid:
                        album_entry['mbid'] = mbid_result.album_mbid
                        album_mbid_path.write_mbid_file(mbid_result.album_mbid)
                if mbid_result.has_artist_mbid:
                    artist_entry = self.find_artist(album_artist)
                    if artist_entry is not None:
                        # we write the artist here if present, this saves an API call to find the artist by name later
                        artist_mbid_path = MBIDPath(os.path.join(Datastore._get_artist_dsdir(artist_entry['artist'])))
                        artist_mbid_path.write_mbid_file(mbid_result.artist_mbid)

    def count_artists(self):
        return len(self.__artists)

    def count_artists_no_mbid(self):
        return len([item for item in self.__artists if item["mbid"] is None])

    def count_albums(self):
        return len(self.__albums)

    def count_albums_no_mbid(self):
        return len([item for item in self.__albums if item["mbid"] is None])

    def find_artist(self, artist_name):
        return next((item for item in self.__artists if item["artist"] == artist_name), None)


class MBIDPath:

    MBID_FILE_NAME = u'mbid.txt'

    def __init__(self, mbid_path):
        self.__mbid_path = mbid_path
        pass

    def has_mbid_file(self):
        mbid_file = os.path.join(self.__mbid_path, self.MBID_FILE_NAME)
        if xbmcvfs.exists(mbid_file):
            return mbid_file
        else:
            return None

    def read_mbid_file(self):
        result = None
        mbid_file = os.path.join(self.__mbid_path, self.MBID_FILE_NAME)
        if xbmcvfs.exists(mbid_file):
            try:
                f = xbmcvfs.File(mbid_file)
                result = f.read()
                f.close()
                if not mbid_finder.MBIDResult.is_mbid(result):  # cleanup invalid files
                    result = None
                    xbmcvfs.delete(mbid_file)
            except IOError:
                pass
        return result

    def write_mbid_file(self, mbid):
        mbid_file = os.path.join(self.__mbid_path, self.MBID_FILE_NAME)
        try:
            f = xbmcvfs.File(mbid_file, 'w')
            result = f.write(utils.smart_utf8(mbid))
            f.close()
        except IOError:
            result = False
            pass
        return result
