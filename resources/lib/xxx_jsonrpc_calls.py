# -*- coding: utf-8 -*-
# script.cdartmanager 
# xxx_jsonrpc_calls.py

import os

import xbmc
import xxx_json_utils
import settings

empty = []


def get_thumbnail_path(database_id, type_):
    settings.log("xxx_jsonrpc_calls.py - Retrieving Thumbnail Path for %s id: %s" % (type_, database_id), xbmc.LOGDEBUG)
    if type_ in ("cover", "cdart", "album") and database_id:
        json_query = '''{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbumDetails", "params": {"properties": ["thumbnail"], "albumid": %d}, "id": 1}''' % database_id
        json_thumb = xxx_json_utils.retrieve_json_dict(json_query, items='albumdetails', force_log=False)
    elif type_ in ("fanart", "clearlogo", "artistthumb", "artist") and database_id:
        json_query = '''{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtistDetails", "params": {"properties": ["thumbnail"], "artistid": %d}, "id": 1}''' % database_id
        json_thumb = xxx_json_utils.retrieve_json_dict(json_query, items='artistdetails', force_log=False)
    else:
        settings.log("xxx_jsonrpc_calls.py - Improper type or database_id", xbmc.LOGDEBUG)
        return empty
    if json_thumb:
        return json_thumb["thumbnail"]
    else:
        return empty


def get_fanart_path(database_id, type_):
    settings.log("xxx_jsonrpc_calls.py - Retrieving Fanart Path for %s id: %s" % (type_, database_id), xbmc.LOGDEBUG)
    if type_ in ("cover", "cdart", "album") and database_id:
        json_query = '''{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbumDetails", "params": {"properties": ["fanart"], "albumid": %d}, "id": 1}''' % database_id
        json_fanart = xxx_json_utils.retrieve_json_dict(json_query, items='albumdetails', force_log=False)
    elif type_ in ("fanart", "clearlogo", "artistthumb", "artist") and database_id:
        json_query = '''{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtistDetails", "params": {"properties": ["fanart"], "artistid": %d}, "id": 1}''' % database_id
        json_fanart = xxx_json_utils.retrieve_json_dict(json_query, items='artistdetails', force_log=False)
    else:
        settings.log("xxx_jsonrpc_calls.py - Improper type or database_id", xbmc.LOGDEBUG)
        return empty
    if json_fanart:
        return json_fanart["fanart"]
    else:
        return empty


def get_all_local_artists(all_artists=True):
    settings.log("xxx_jsonrpc_calls.py - Retrieving all local artists", xbmc.LOGDEBUG)
    if all_artists:
        json_query = '''{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": { "albumartistsonly": false }, "id": 1}'''
    else:
        json_query = '''{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": { "albumartistsonly": true }, "id": 1}'''
    json_artists = xxx_json_utils.retrieve_json_dict(json_query, items='artists', force_log=False)
    if json_artists:
        return json_artists
    else:
        return empty


def retrieve_artist_details(artist_id):
    settings.log("xxx_jsonrpc_calls.py - Retrieving Artist Details", xbmc.LOGDEBUG)
    json_query = '''{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtistDetails", "params": {"properties": ["musicbrainzartistid"], "artistid": %d}, "id": 1}''' % artist_id
    json_artist_details = xxx_json_utils.retrieve_json_dict(json_query, items='artistdetails', force_log=False)
    if json_artist_details:
        return json_artist_details
    else:
        return empty


def retrieve_album_list():
    settings.log("xxx_jsonrpc_calls.py - Retrieving Album List", xbmc.LOGDEBUG)
    json_query = '''{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": { "limits": { "start": 0 }, "properties": ["title", "artist", "musicbrainzalbumid", "musicbrainzalbumartistid"], "sort": {"order":"ascending"}}, "id": 1}'''
    json_albums = xxx_json_utils.retrieve_json_dict(json_query, items='albums', force_log=False)
    if json_albums:
        return json_albums
    else:
        return empty


def retrieve_album_details(album_id):
    settings.log("xxx_jsonrpc_calls.py - Retrieving Album Details", xbmc.LOGDEBUG)
    album_details = []
    json_query = '''{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbumDetails", "params": {"properties": ["artist", "title", "musicbrainzalbumid", "musicbrainzalbumartistid"], "albumid": %d}, "id": 1}''' % album_id
    json_album_details = xxx_json_utils.retrieve_json_dict(json_query, items='albumdetails', force_log=False)
    if json_album_details:
        album_details.append(json_album_details)
        return album_details
    else:
        return empty


def get_album_path(album_id):
    settings.log("xxx_jsonrpc_calls.py - Retrieving Album Path", xbmc.LOGDEBUG)
    paths = []
    albumartistmbids = []
    albumreleasembids = []
    json_query = '''{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": { "properties": ["file", "musicbrainzalbumartistid", "musicbrainzalbumid"], "filter": { "albumid": %d }, "sort": {"method":"path","order":"ascending"} }, "id": 1}''' % album_id
    json_songs_detail = xxx_json_utils.retrieve_json_dict(json_query, items='songs', force_log=False)
    if json_songs_detail:
        for song in json_songs_detail:
            path = os.path.dirname(song['file'])
            paths.append(path)
            albumartistmbid = song['musicbrainzalbumartistid']
            albumartistmbids.append(albumartistmbid)
            albumreleasembid = song['musicbrainzalbumid']
            albumreleasembids.append(albumreleasembid)
        return paths, albumartistmbids, albumreleasembids
    else:
        return empty
