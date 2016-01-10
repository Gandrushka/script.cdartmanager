import xbmc
import settings


def _retrieve_json_dict(json_query, items='items', force_log=False):
    empty = []
    settings.log("JSONRPC Query -\n%s" % json_query, xbmc.LOGDEBUG)
    response = xbmc.executeJSONRPC(json_query)
    if force_log:
        settings.log("retrieve_json_dict - JSONRPC -\n%s" % response)
    if response.startswith("{"):
        response = eval(response)
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
        return json_artists
    else:
        return []


def get_albums():
    settings.log("Retrieving Album List")
    json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": { "limits": { "start": 0 }, ' \
                 '"properties": ["title", "artist", "artistid", "musicbrainzalbumid", "musicbrainzalbumartistid"], "sort": {"order":"ascending"}}, "id": 1}'
    json_albums = _retrieve_json_dict(json_query, items='albums', force_log=False)

    if json_albums:
        # here the path should be added...

        return json_albums
    else:
        return []
