import xbmc
import xbmcvfs
import os
import settings
import json
import constants
import utils


def _retrieve_json_dict(json_query, items='items', force_log=False):
    empty = []
    settings.log("JSONRPC Query -\n%s" % json_query, xbmc.LOGDEBUG)
    response = xbmc.executeJSONRPC(json_query)
    if force_log:
        settings.log("retrieve_json_dict - JSONRPC -\n%s" % response)
    if response.startswith("{"):
        response = json.loads(response)
        try:
            if "result" in response:
                result = response['result']
                json_dict = result[items]
                return json_dict
            else:
                settings.log("retrieve_json_dict - No response from XBMC", xbmc.LOGNOTICE)
                settings.log(response)
                return None
        except:
            settings.log("retrieve_json_dict - JSONRPC -\n%s" % response, xbmc.LOGNOTICE)
            settings.log("retrieve_json_dict - Error trying to get json response", xbmc.LOGNOTICE)
            return empty
    else:
        return empty


def get_artists(album_artists_only=True):
    settings.log("Retrieving all local artists")
    json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": { "albumartistsonly": %s, "properties":["musicbrainzartistid"], ' \
                 '"sort":{ "order": "ascending", "method": "label", "ignorearticle": true }}, "id": 1}' % str(album_artists_only).lower()
    json_artists = _retrieve_json_dict(json_query, items='artists', force_log=False)
    if json_artists:
        result = {}
        for artist in json_artists:
            result[artist['artistid']] = artist
        return result
    else:
        return {}


def get_albums():
    settings.log("Retrieving Album List")
    json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": { "limits": { "start": 0 }, ' \
                 '"properties": ["title", "artist", "artistid", "musicbrainzalbumid", "musicbrainzalbumartistid"], "sort": {"order":"ascending"}}, "id": 1}'
    json_albums = _retrieve_json_dict(json_query, items='albums', force_log=False)

    if json_albums:
        result = {}
        for album in json_albums:
            result[album['albumid']] = album
        return result
    else:
        return {}


def get_albumpaths(album_id):
    json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": { "properties": ["file"], ' \
                 '"filter": { "albumid": %d } }, "id": 1}' % album_id
    json_songs_detail = _retrieve_json_dict(json_query, items='songs', force_log=False)
    paths = set()
    for song in json_songs_detail:
        if 'file' in song:
            path = os.path.dirname(song['file'])
            paths.add(path)
    album_paths = list()
    for path in paths:
        album_paths.append(AlbumPath(path))
    return album_paths


class AlbumPath:

    def __init__(self, path, *args, **kwargs):
        self.__path = path
        self.__cover_file = os.path.join(path, constants.ART_FILENAME_ALBUM_COVER)
        self.__cdart_file = os.path.join(path, constants.ART_FILENAME_ALBUM_CDART)

    def to_json(self):
        return {self.path: {'has_cover': self.has_cover, 'has_cdart': self.has_cdart}}

    @property
    def path(self):
        return self.__path

    @property
    def cover_file_path(self):
        return self.__cover_file

    @property
    def cdart_file_path(self):
        return self.__cdart_file

    @property
    def has_cover(self):
        return xbmcvfs.exists(self.cover_file_path)

    @property
    def has_cdart(self):
        return xbmcvfs.exists(self.cdart_file_path)
