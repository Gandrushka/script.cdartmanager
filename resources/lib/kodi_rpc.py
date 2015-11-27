import xbmc
import settings


def _retrieve_json_dict(json_query, items='items', force_log=False):
    empty = []
    settings.log("[xxx_json_utils.py] - JSONRPC Query -\n%s" % json_query)
    response = xbmc.executeJSONRPC(json_query)
    if force_log:
        settings.log("[xxx_json_utils.py] - retrieve_json_dict - JSONRPC -\n%s" % response)
    if response.startswith("{"):
        response = eval(response)
        try:
            if "result" in response:
                result = response['result']
                json_dict = result[items]
                return json_dict
            else:
                settings.log("[xxx_json_utils.py] - retrieve_json_dict - No response from XBMC", xbmc.LOGNOTICE)
                settings.log(response)
                return None
        except:
            settings.log("[xxx_json_utils.py] - retrieve_json_dict - JSONRPC -\n%s" % response, xbmc.LOGNOTICE)
            settings.log("[xxx_json_utils.py] - retrieve_json_dict - Error trying to get json response", xbmc.LOGNOTICE)
            return empty
    else:
        return empty


def get_artists(all_artists=True):
    settings.log("xxx_jsonrpc_calls.py - Retrieving all local artists")
    json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": { "albumartistsonly": %s, "properties":["musicbrainzartistid"], "sort":{ "order": "ascending", "method": "label", "ignorearticle": true }}, "id": 1}' % str(all_artists).lower()
    json_artists = _retrieve_json_dict(json_query, items='artists', force_log=False)
    if json_artists:
        return json_artists
    else:
        return []


def get_albums():
    settings.log("xxx_jsonrpc_calls.py - Retrieving Album List")
    json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": { "limits": { "start": 0 }, "properties": ["title", "artist", "musicbrainzalbumid", "musicbrainzalbumartistid"], "sort": {"order":"ascending"}}, "id": 1}'
    json_albums = _retrieve_json_dict(json_query, items='albums', force_log=False)
    if json_albums:
        return json_albums
    else:
        return []
