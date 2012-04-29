# -*- coding: utf-8 -*-
# script.cdart.manager 
# pre-eden code

import xbmc, xbmcaddon, xbmcvfs
import os
from json_utils import retrieve_json_dict

def get_all_local_artists():
    xbmc.log( "[script.cdartmanager] - pre_eden_code - Retrieving all local artists", xbmc.LOGDEBUG )
    json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "id": 1}'
    json_artists = retrieve_json_dict(json_query, items='artists', force_log=False )
    if json_artists:
        return json_artists
    else:
        return None
        
def retrieve_album_list():
    xbmc.log( "[script.cdartmanager] - pre_eden_code - Retrieving Album List"        , xbmc.LOGDEBUG )
    json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": { "limits": { "start": 0 }, "properties": ["title", "artist"], "sort": {"order":"ascending"}}, "id": 1}'
    json_albums = retrieve_json_dict(json_query, items='albums', force_log=False )
    if json_albums:
        return json_albums, len(json_albums)
    else:
        return None, 0
    
def retrieve_album_details( album_id ):
    xbmc.log( "[script.cdartmanager] - pre_eden_code - Retrieving Album Path", xbmc.LOGDEBUG )
    album_details = []
    json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbumDetails", "params": {"properties": ["artist", "title"], "albumid": %d}, "id": 1}' % album_id
    json_album_details = retrieve_json_dict(json_query, items='albumdetails', force_log=False )
    if json_album_details:
        album_details.append( json_album_details )
        return album_details
    else:
        return None

def get_album_path( album_id ):
    xbmc.log( "[script.cdartmanager] - pre_eden_code - Retrieving Album Path", xbmc.LOGDEBUG )
    paths = []
    json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": {"albumid": %d, "properties": ["file"], "sort": {"method":"fullpath","order":"ascending"}}, "id": 1}' % album_id
    json_songs_detail = retrieve_json_dict(json_query, items='songs', force_log=False )
    if json_songs_detail:
        for song in json_songs_detail:
            path = os.path.dirname( song['file'] )
            paths.append( path )
        return paths
    else:
        return None
