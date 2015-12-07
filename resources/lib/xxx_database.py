# -*- coding: utf-8 -*-

import os
import re
import traceback

import xbmc
import xbmcvfs

# DANGER: this must be defined BEFORE local imports to avoid circulars.
#         Of course after restructuring is finished there will be
#         no need for any database related imports in other modules... mhh.
import resources.lib.utils

try:
    from sqlite3 import dbapi2 as sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3

import constants
import settings
import xxx_musicbrainz
import xxx_utils
import xxx_jsonrpc_calls
import utils

__settings__ = settings.Settings()




def __create_new_db():
    conn = __connect()
    c = conn.cursor()
    c.execute('CREATE TABLE counts(local_artists INTEGER, artists INTEGER, albums INTEGER, cdarts INTEGER, version TEXT, datecode INTEGER)')
    c.execute('CREATE TABLE lalist(local_id INTEGER, name TEXT, musicbrainz_artistid TEXT, fanarttv_has_art TEXT)')  # create local album artists database
    c.execute('CREATE TABLE alblist(album_id INTEGER, title TEXT, artist TEXT, path TEXT, cdart TEXT, cover TEXT, '
              'disc INTEGER, musicbrainz_albumid TEXT, musicbrainz_artistid TEXT)')  # create local album database
    c.execute('CREATE TABLE unqlist(title TEXT, disc INTEGER, artist TEXT, path TEXT, cdart TEXT)')  # create unique database
    c.execute('CREATE TABLE local_artists(local_id INTEGER, name TEXT, musicbrainz_artistid TEXT, fanarttv_has_art TEXT)')
    conn.commit()
    c.close()
    conn.close()


def __connect():
    return sqlite3.connect(__settings__.getDatabaseFile())


# # # OLD # # #


def user_updates(details, type_):
    settings.log("Storing User edit", xbmc.LOGNOTICE)
    conn = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn.cursor()
    c.execute('''CREATE table IF NOT EXISTS artist_updates(local_id INTEGER, name TEXT, musicbrainz_artistid TEXT)''')
    c.execute(
        '''CREATE table IF NOT EXISTS album_updates(album_id INTEGER, title TEXT, artist TEXT, path TEXT, musicbrainz_albumid TEXT, musicbrainz_artistid TEXT)''')
    if type_ == "artist":
        settings.log("Storing artist update", xbmc.LOGNOTICE)
        try:
            c.execute(
                '''SELECT DISTINCT musicbrainz_artistid FROM artist_updates WHERE local_id=%s''' % details["local_id"])
            db_details = c.fetchall()
            if db_details:
                settings.log("Updating existing artist edit", xbmc.LOGNOTICE)
                c.execute('''UPDATE artist_updates SET musicbrainz_artistid="%s", name="%s" WHERE local_id=%s''' % (
                    details["musicbrainz_artistid"], details["name"], details["local_id"]))
            else:
                settings.log("Storing new artist edit", xbmc.LOGNOTICE)
                c.execute('''INSERT INTO artist_updates(local_id, name, musicbrainz_artistid) values (?, ?, ?)''',
                          (details["local_id"], details["name"], details["musicbrainz_artistid"]))
        except:
            settings.log("Error updating artist_updates table", xbmc.LOGERROR)
            traceback.print_exc()
        try:
            c.execute('''UPDATE lalist SET musicbrainz_artistid="%s", name="%s" WHERE local_id=%s''' % (
                details["musicbrainz_artistid"], details["name"], details["local_id"]))
        except:
            settings.log("Error updating album artist table", xbmc.LOGERROR)
            traceback.print_exc()
        try:
            c.execute('''UPDATE alblist SET musicbrainz_artistid="%s", artist="%s" WHERE artist="%s"''' % (
                details["musicbrainz_artistid"], details["name"], details["name"]))
        except:
            settings.log("Error updating album table", xbmc.LOGERROR)
            traceback.print_exc()
        try:
            c.execute('''UPDATE local_artists SET musicbrainz_artistid="%s", name="%s" WHERE local_id=%s''' % (
                details["musicbrainz_artistid"], details["name"], details["local_id"]))
        except:
            settings.log("Error updating local artist table", xbmc.LOGERROR)
            traceback.print_exc()
    if type_ == "album":
        settings.log("Storing album update", xbmc.LOGNOTICE)
        try:
            c.execute('''SELECT DISTINCT album_id FROM album_updates WHERE album_id=%s and path="%s"''' % (
                details["local_id"], xxx_utils.get_unicode(details["path"])))
            db_details = c.fetchall()
            print db_details
            if db_details:
                settings.log("Updating existing album edit", xbmc.LOGNOTICE)
                c.execute(
                    '''UPDATE album_updates SET artist="%s", title="%s", musicbrainz_albumid="%s", musicbrainz_artistid="%s" WHERE album_id=%s and path="%s"''' % (
                        xxx_utils.get_unicode(details["artist"]), xxx_utils.get_unicode(details["title"]), details["musicbrainz_albumid"],
                        details["musicbrainz_artistid"], details["local_id"], xxx_utils.get_unicode(details["path"])))
            else:
                settings.log("Storing new album edit", xbmc.LOGNOTICE)
                c.execute(
                    '''INSERT INTO album_updates(album_id, title, artist, path, musicbrainz_albumid, musicbrainz_artistid) values (?, ?, ?, ?, ?, ?)''',
                    (details["local_id"], xxx_utils.get_unicode(details["title"]), xxx_utils.get_unicode(details["artist"]),
                     xxx_utils.get_unicode(details["path"]), details["musicbrainz_albumid"], details["musicbrainz_artistid"]))
        except:
            settings.log("Error updating album_updates table", xbmc.LOGERROR)
            traceback.print_exc()
        try:
            c.execute(
                '''UPDATE alblist SET artist="%s", title="%s", musicbrainz_albumid="%s", musicbrainz_artistid="%s" WHERE album_id=%s and path="%s"''' % (
                    xxx_utils.get_unicode(details["artist"]), xxx_utils.get_unicode(details["title"]), details["musicbrainz_albumid"],
                    details["musicbrainz_artistid"], details["local_id"], xxx_utils.get_unicode(details["path"])))
        except:
            settings.log("Error updating album table", xbmc.LOGERROR)
            traceback.print_exc()
    conn.commit()
    c.close()


def restore_user_updates():
    try:
        conn = sqlite3.connect(__settings__.getDatabaseFile())
        c = conn.cursor()
        c.execute(
            '''UPDATE lalist SET musicbrainz_artistid = (SELECT artist_updates.musicbrainz_artistid FROM artist_updates WHERE artist_updates.local_id = lalist.local_id ) WHERE EXISTS ( SELECT * FROM artist_updates WHERE artist_updates.name = lalist.name )''')
        c.execute(
            '''UPDATE local_artists SET musicbrainz_artistid = (SELECT artist_updates.musicbrainz_artistid FROM artist_updates WHERE artist_updates.local_id = local_artists.local_id ) WHERE EXISTS ( SELECT * FROM artist_updates WHERE artist_updates.name = local_artists.name )''')
        c.execute(
            '''UPDATE alblist SET musicbrainz_artistid = (SELECT album_updates.musicbrainz_artistid FROM album_updates WHERE album_updates.album_id = alblist.album_id ) WHERE EXISTS ( SELECT * FROM album_updates WHERE album_updates.album_id = alblist.album_id )''')
        c.execute(
            '''UPDATE alblist SET musicbrainz_albumid = (SELECT album_updates.musicbrainz_albumid FROM album_updates WHERE album_updates.album_id = alblist.album_id ) WHERE EXISTS ( SELECT * FROM album_updates WHERE album_updates.album_id = alblist.album_id )''')
        conn.commit()
        c.close()
    except:
        traceback.print_exc()


def artist_list_to_string(artist):
    if not (type(artist) is list):
        artist_string = artist
    else:
        if len(artist) > 1:
            artist_string = " / ".join(artist)
        else:
            artist_string = "".join(artist)
    return artist_string


def artwork_search(cdart_url, id_, disc, type_):
    settings.log("Finding Artwork")
    art = {}
    for item in cdart_url:
        if item["musicbrainz_albumid"] == id_:
            if type_ == "cover":
                art = item
                break
            elif int(item["disc"]) == int(disc) and type_ == "cdart":
                art = item
                break
    return art


def get_xbmc_database_info(background=False):
    settings.log("Retrieving Album Info from XBMC's Music DB")
    xxx_utils.dialog_msg("create", heading=utils.lang(32021), line1=utils.lang(32105), background=background)
    album_list = xxx_jsonrpc_calls.retrieve_album_list()
    if not album_list:
        xxx_utils.dialog_msg("close", background=background)
        return None
    total = len(album_list)
    album_detail_list = retrieve_album_details_full(album_list, total, background=background, simple=False, update=False)
    xxx_utils.dialog_msg("close", background=background)
    return album_detail_list


def retrieve_album_details_full(album_list, total, background=False, simple=False, update=False):
    settings.log("Retrieving Album Details")
    album_detail_list = []
    album_count = 0
    percent = 1
    try:
        for detail in album_list:
            if not detail["title"] and detail["label"]:  # check to see if title is empty and label contains something
                detail["title"] = detail["label"]
            if xxx_utils.dialog_msg("iscanceled", background=background):
                break
            album_count += 1
            percent = int((album_count / float(total)) * 100)
            xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(20186),
                                 line2="%s: %s" % (utils.lang(32138), (xxx_utils.get_unicode(detail['title']))),
                                 line3="%s #:%6s      %s%6s" % (utils.lang(32039), album_count, utils.lang(32045), total),
                                 background=background)
            try:
                album_id = detail['local_id']
            except:
                album_id = detail['albumid']
            albumdetails = xxx_jsonrpc_calls.retrieve_album_details(album_id)
            if not albumdetails:
                continue
            for album in albumdetails:
                if xxx_utils.dialog_msg("iscanceled", background=background):
                    break
                album_artist = {}
                previous_path = ""
                mbid_match = False
                albumrelease_mbid = ""
                albumartist_mbid = ""
                if not update:
                    paths, albumartistmbids, albumreleasembids = xxx_jsonrpc_calls.get_album_path(album_id)
                    if albumartistmbids:
                        albumartist_mbid = albumartistmbids[0]
                        for albumartistmbid in albumartistmbids:
                            if albumartist_mbid == albumartistmbid:
                                mbid_match = True
                                settings.log("Found an Artist MBID in the Database: %s" % albumartist_mbid)
                                continue
                            else:
                                mbid_match = False
                        if not mbid_match:
                            albumartist_mbid = ""
                    if albumreleasembids:
                        albumrelease_mbid = albumreleasembids[0]
                        settings.log("Found an Album Release MBID in the Database: %s" % albumrelease_mbid)
                    if not paths:
                        continue
                else:
                    paths = [detail['path']]
                for path in paths:
                    try:
                        if xxx_utils.dialog_msg("iscanceled", background=background):
                            break
                        album_artist = {}
                        if path == previous_path:
                            continue
                        else:
                            # Helix: paths MUST end with trailing slash
                            if xbmcvfs.exists(os.path.join(path, '')):
                                settings.log("Path Exists")
                                try:
                                    album_artist["local_id"] = detail['local_id']  # for database update
                                except:
                                    album_artist["local_id"] = detail['albumid']
                                title = detail['title']
                                album_artist["artist"] = xxx_utils.get_unicode(
                                    artist_list_to_string(album['artist']).split(" / ")[0])
                                album_artist["path"] = xxx_utils.get_unicode(path)
                                album_artist["cdart"] = xbmcvfs.exists(
                                    os.path.join(path, "cdart.png").replace("\\\\", "\\"))
                                album_artist["cover"] = xbmcvfs.exists(
                                    os.path.join(path, "folder.jpg").replace("\\\\", "\\"))
                                previous_path = path
                                path_match = re.search("(?:\\\\|/| - )(?:disc|cd)(?:\s|-|_|)([0-9]{0,3})",
                                                       path.replace("\\\\", "\\"), re.I)
                                title_match = re.search(
                                    "(.*?)(?:[\s]|[\(]|[\s][\(])(?:disc|cd)(?:[\s]|)([0-9]{0,3})(?:[\)]?.*?)", title,
                                    re.I)
                                if title_match:
                                    if len(title_match.groups()) > 1:
                                        if title_match.group(2):
                                            settings.log("Title has CD count")
                                            settings.log("    Disc %s" % title_match.group(2))
                                            album_artist["disc"] = int(title_match.group(2))
                                            album_artist["title"] = xxx_utils.get_unicode(
                                                (title_match.group(1).replace(" -", "")).rstrip())
                                        else:
                                            if path_match:
                                                if len(path_match.groups()) > 0:
                                                    if path_match.group(1):
                                                        settings.log("Path has CD count")
                                                        settings.log("    Disc %s" % repr(path_match.group(1)))
                                                        album_artist["disc"] = int(path_match.group(1))
                                                    else:
                                                        album_artist["disc"] = 1
                                                else:
                                                    album_artist["disc"] = 1
                                            else:
                                                album_artist["disc"] = 1
                                            album_artist["title"] = xxx_utils.get_unicode((title.replace(" -", "")).rstrip())
                                    else:
                                        if path_match:
                                            if len(path_match.groups()) > 0:
                                                if path_match.group(1):
                                                    settings.log("Path has CD count")
                                                    settings.log("    Disc %s" % repr(path_match.group(1)))
                                                    album_artist["disc"] = int(path_match.group(1))
                                                else:
                                                    album_artist["disc"] = 1
                                            else:
                                                album_artist["disc"] = 1
                                        else:
                                            album_artist["disc"] = 1
                                        album_artist["title"] = xxx_utils.get_unicode((title.replace(" -", "")).rstrip())
                                else:
                                    if path_match:
                                        if len(path_match.groups()) > 0:
                                            if path_match.group(1):
                                                settings.log("Path has CD count")
                                                settings.log("    Disc %s" % repr(path_match.group(1)))
                                                album_artist["disc"] = int(path_match.group(1))
                                            else:
                                                album_artist["disc"] = 1
                                        else:
                                            album_artist["disc"] = 1
                                    else:
                                        album_artist["disc"] = 1
                                    album_artist["title"] = xxx_utils.get_unicode((title.replace(" -", "")).rstrip())
                                settings.log("Album Title: %s" % album_artist["title"])
                                settings.log("Album Artist: %s" % album_artist["artist"])
                                settings.log("Album ID: %s" % album_artist["local_id"])
                                settings.log("Album Path: %s" % album_artist["path"])
                                settings.log("cdART Exists?: %s" % ("False", "True")[album_artist["cdart"]])
                                settings.log("Cover Art Exists?: %s" % ("False", "True")[album_artist["cover"]])
                                settings.log("Disc #: %s" % album_artist["disc"])
                                if not simple:
                                    album_artist["musicbrainz_artistid"] = ""
                                    album_artist["musicbrainz_albumid"] = ""
                                    if albumartist_mbid:
                                        album_artist["musicbrainz_artistid"] = albumartist_mbid
                                    if albumrelease_mbid:
                                        album_artist["musicbrainz_albumid"] = xxx_musicbrainz.get_musicbrainz_release_group(
                                            albumrelease_mbid)
                                    if not album_artist["musicbrainz_albumid"]:
                                        try:
                                            musicbrainz_albuminfo, discard = xxx_musicbrainz.get_musicbrainz_album(
                                                album_artist["title"], album_artist["artist"], 0, 1)
                                            album_artist["musicbrainz_albumid"] = musicbrainz_albuminfo["id"]
                                            album_artist["musicbrainz_artistid"] = musicbrainz_albuminfo["artist_id"]
                                        except:
                                            traceback.print_exc()
                                    settings.log("MusicBrainz AlbumId: %s" % album_artist["musicbrainz_albumid"])
                                    settings.log("MusicBrainz ArtistId: %s" % album_artist["musicbrainz_artistid"],
                                                 xbmc.LOGDEBUG)
                                album_detail_list.append(album_artist)

                            else:
                                settings.log("Path does not exist: %s" % repr(path))
                                continue
                    except:
                        settings.log("Error Occured")
                        settings.log("Title: %s" % detail['title'])
                        settings.log("Path: %s" % path)
                        traceback.print_exc()
    except:
        settings.log("Error Occured")
        traceback.print_exc()
        xxx_utils.dialog_msg("close", background=background)
    return album_detail_list


def get_album_cdart(album_path):
    settings.log("Retrieving cdART status")
    if xbmcvfs.exists(os.path.join(album_path, "cdart.png").replace("\\\\", "\\")):
        return True
    else:
        return False


def get_album_coverart(album_path):
    settings.log("Retrieving cover art status")
    if xbmcvfs.exists(os.path.join(album_path, "folder.jpg").replace("\\\\", "\\")):
        return True
    else:
        return False


def store_alblist(local_album_list, background=False):
    settings.log("Storing alblist")
    album_count = 0
    cdart_existing = 0
    conn = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn.cursor()
    percent = 0
    try:
        for album in local_album_list:
            xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(20186),
                                 line2="%s: %s" % (utils.lang(32138), xxx_utils.get_unicode(album["title"])),
                                 line3="%s%6s" % (utils.lang(32100), album_count), background=background)
            settings.log("Album Count: %s" % album_count)
            settings.log("Album ID: %s" % album["local_id"])
            settings.log("Album Title: %s" % album["title"])
            settings.log("Album Artist: %s" % album["artist"])
            settings.log("Album Path: %s" % album["path"].replace("\\\\", "\\"))
            settings.log("cdART Exist?: %s" % ("False", "True")[album["cdart"]])
            settings.log("Cover Art Exist?: %s" % ("False", "True")[album["cover"]])
            settings.log("Disc #: %s" % album["disc"])
            settings.log("MusicBrainz AlbumId: %s" % album["musicbrainz_albumid"])
            settings.log("MusicBrainz ArtistId: %s" % album["musicbrainz_artistid"])
            try:
                if album["cdart"]:
                    cdart_existing += 1
                album_count += 1
                c.execute(
                    '''insert into alblist(album_id, title, artist, path, cdart, cover, disc, musicbrainz_albumid, musicbrainz_artistid) values (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (album["local_id"], xxx_utils.get_unicode(album["title"]), xxx_utils.get_unicode(album["artist"]),
                     xxx_utils.get_unicode(album["path"].replace("\\\\", "\\")), ("False", "True")[album["cdart"]],
                     ("False", "True")[album["cover"]], album["disc"], album["musicbrainz_albumid"],
                     album["musicbrainz_artistid"]))
            except:
                settings.log("Error Saving to Database")
                traceback.print_exc()
            if xxx_utils.dialog_msg("iscanceled", background=background):
                break
    except:
        settings.log("Error Saving to Database")
        traceback.print_exc()
    conn.commit()
    c.close()
    settings.log("Finished Storing ablist")
    return album_count, cdart_existing


def recount_cdarts():
    settings.log("Recounting cdARTS")
    cdart_existing = 0
    conn = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn.cursor()
    c.execute("""SELECT title, cdart FROM alblist""")
    db = c.fetchall()
    for item in db:
        if resources.lib.utils.is_true(item[1]):
            cdart_existing += 1
    c.close()
    return cdart_existing


def store_lalist(local_artist_list, count_artist_local):
    settings.log("Storing lalist")
    conn = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn.cursor()
    artist_count = 0
    c.execute('''DROP table IF EXISTS lalist''')
    c.execute(
        '''CREATE TABLE lalist(local_id INTEGER, name TEXT, musicbrainz_artistid TEXT, fanarttv_has_art TEXT)''')  # create local artists database
    for artist in local_artist_list:
        try:
            try:
                c.execute(
                    '''insert into lalist(local_id, name, musicbrainz_artistid, fanarttv_has_art) values (?, ?, ?, ?)''',
                    (artist["local_id"], unicode(artist["name"], 'utf-8', ), artist["musicbrainz_artistid"],
                     artist["has_art"]))
            except TypeError:
                c.execute(
                    '''insert into lalist(local_id, name, musicbrainz_artistid, fanarttv_has_art) values (?, ?, ?, ?)''',
                    (
                        artist["local_id"], xxx_utils.get_unicode(artist["name"]), artist["musicbrainz_artistid"], artist["has_art"]))
            except:
                traceback.print_exc()
            artist_count += 1
            percent = int((artist_count / float(count_artist_local)) * 100)
        except:
            traceback.print_exc()
    conn.commit()
    c.close()
    settings.log("Finished Storing lalist")
    return artist_count


def retrieve_fanarttv_datecode():
    query = "SELECT datecode FROM counts"
    conn_l = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn_l.cursor()
    c.execute(query)
    result = c.fetchall()
    c.close()
    datecode = result[0][0]
    return datecode


def store_fanarttv_datecode(datecode):
    local_artist_count, album_count, artist_count, cdart_existing = new_local_count()
    store_counts(local_artist_count, artist_count, album_count, cdart_existing, datecode=datecode)


def retrieve_distinct_album_artists():
    settings.log("Retrieving Distinct Album Artist")
    album_artists = []
    conn = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn.cursor()
    c.execute("""SELECT DISTINCT artist, musicbrainz_artistid FROM alblist""")
    db = c.fetchall()
    for item in db:
        artist = {"name": xxx_utils.get_unicode(item[0]), "musicbrainz_artistid": xxx_utils.get_unicode(item[1])}
        album_artists.append(artist)
    c.close()
    settings.log("Finished Retrieving Distinct Album Artists")
    return album_artists


def store_counts(local_artists_count, artist_count, album_count, cdart_existing, datecode=0):
    settings.log("Storing Counts", xbmc.LOGNOTICE)
    settings.log("    Album Count: %s" % album_count, xbmc.LOGNOTICE)
    settings.log("    Album Artist Count: %s" % artist_count, xbmc.LOGNOTICE)
    settings.log("    Local Artist Count: %s" % local_artists_count, xbmc.LOGNOTICE)
    settings.log("    cdARTs Existing Count: %s" % cdart_existing, xbmc.LOGNOTICE)
    settings.log("    Unix Date Code: %s" % datecode, xbmc.LOGNOTICE)
    conn = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn.cursor()
    try:
        c.execute('''DROP table IF EXISTS counts''')
    except:
        # table missing
        traceback.print_exc()
    try:
        c.execute(
            '''CREATE TABLE counts(local_artists INTEGER, artists INTEGER, albums INTEGER, cdarts INTEGER, version TEXT, datecode INTEGER)''')
    except:
        traceback.print_exc()
    if datecode == 0:
        c.execute('''insert into counts(local_artists, artists, albums, cdarts, version) values (?, ?, ?, ?, ?)''',
                  (local_artists_count, artist_count, album_count, cdart_existing, constants.DB_VERSION))
    else:
        c.execute(
            '''insert into counts(local_artists, artists, albums, cdarts, version, datecode) values (?, ?, ?, ?, ?, ?)''',
            (local_artists_count, artist_count, album_count, cdart_existing, constants.DB_VERSION, datecode))
    conn.commit()
    c.close()
    settings.log("Finished Storing Counts")


def check_local_albumartist(album_artist, local_artist_list, background=False):
    settings.log("Checking Local Artists", xbmc.LOGNOTICE)
    artist_count = 0
    percent = 0
    found = False
    local_album_artist_list = []
    for artist in album_artist:  # match album artist to local artist id
        album_artist_1 = {}
        name = ""
        name = xxx_utils.get_unicode(artist_list_to_string(artist["name"]))
        artist_count += 1
        for local in local_artist_list:
            xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(20186), line2="%s" % utils.lang(32101),
                                 line3="%s:%s" % (utils.lang(32038), (xxx_utils.get_unicode(artist_list_to_string(local["artist"])))),
                                 background=background)
            if xxx_utils.dialog_msg("iscanceled", background=background):
                break
            if name == xxx_utils.get_unicode(artist_list_to_string(local["artist"])):
                id_ = local["artistid"]
                found = True
                break
        if found:
            album_artist_1["name"] = name  # store name and
            album_artist_1["local_id"] = id_  # local id
            album_artist_1["musicbrainz_artistid"] = artist["musicbrainz_artistid"]
            album_artist_1["has_art"] = "False"
            local_album_artist_list.append(album_artist_1)
        else:
            settings.log("Artist Not Found:")
            try:
                settings.log(repr(artist_list_to_string(artist["name"])))
            except:
                traceback.print_exc()
    return local_album_artist_list, artist_count


# def database_setup(background=False):
#     loglevel = xbmc.LOGNOTICE
#     cdart_existing = 0
#     album_count = 0
#     artist_count = 0
#     local_artist_count = 0
#     settings.log("Setting Up Database", loglevel)
#     settings.log("    addon_work_path: %s" % __settings__.getWorkBasePath(), loglevel)
#
#     if not xbmcvfs.exists(__settings__.getWorkFile("settings.xml")):
#         xxx_utils.dialog_msg("ok", heading=utils.lang(32071), line1=utils.lang(32072), line2=utils.lang(32073), background=background)
#         settings.log("Settings not set, aborting database creation", loglevel)
#         return album_count, artist_count, cdart_existing
#
#     local_album_list = get_xbmc_database_info(background=background)
#     if not local_album_list:
#         xxx_utils.dialog_msg("ok", heading=utils.lang(32130), line1=utils.lang(32131), background=background)
#         settings.log("XBMC Music Library does not exist, aborting database creation", loglevel)
#         return album_count, artist_count, cdart_existing
#
#     xxx_utils.dialog_msg("create", heading=utils.lang(32021), line1=utils.lang(20186), background=background)
#     # Onscreen Dialog - Creating Addon Database
#     settings.log("Creating tables...", loglevel)
#     __create_new_db()
#     settings.log("tables created.", loglevel)
#     store_counts(0, 0, 0, 0)
#     album_count, cdart_existing = store_alblist(local_album_list, background=background)  # store album details first
#     album_artist = retrieve_distinct_album_artists()  # then retrieve distinct album artists
#     local_artist_list = xxx_jsonrpc_calls.get_all_local_artists()  # retrieve local artists(to get idArtist)
#     local_album_artist_list, artist_count = check_local_albumartist(album_artist, local_artist_list, background=background)
#     count = store_lalist(local_album_artist_list, artist_count)  # then store in database
#     if __settings__.getExpEnableAllArtits():
#         local_artist_count = build_local_artist_table(background=background)
#     store_counts(local_artist_count, artist_count, album_count, cdart_existing)
#     if xxx_utils.dialog_msg("iscanceled", background=background):
#         xxx_utils.dialog_msg("close", background=background)
#         ok = xxx_utils.dialog_msg("ok", heading=utils.lang(32050), line1=utils.lang(32051), line2=utils.lang(32052),
#                                   line3=utils.lang(32053), background=background)
#     settings.log("Finished Storing Database", loglevel)
#     xxx_utils.dialog_msg("close", background=background)
#     return album_count, artist_count, cdart_existing


# retrieve the addon's database - saves time by no needing to search system for infomation on every addon access
def get_local_albums_db(artist_name, background=False):
    settings.log("Retrieving Local Albums Database")
    local_album_list = []
    conn_l = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn_l.cursor()
    try:
        if artist_name == "all artists":
            xxx_utils.dialog_msg("create", heading=utils.lang(32102), line1=utils.lang(20186), background=background)
            query = '''SELECT DISTINCT album_id, title, artist, path, cdart, cover, disc, musicbrainz_albumid, musicbrainz_artistid FROM alblist ORDER BY artist, title ASC'''
            c.execute(query)
        else:
            query = '''SELECT DISTINCT album_id, title, artist, path, cdart, cover, disc, musicbrainz_albumid, musicbrainz_artistid FROM alblist WHERE artist="%s" ORDER BY title ASC''' % artist_name
            try:
                c.execute(query)
            except sqlite3.OperationalError:
                try:
                    query = '''SELECT DISTINCT album_id, title, artist, path, cdart, cover, disc, musicbrainz_albumid, musicbrainz_artistid FROM alblist WHERE artist="%s" ORDER BY title ASC''' % artist_name
                    c.execute(query)
                except sqlite3.OperationalError:
                    query = '''SELECT DISTINCT album_id, title, artist, path, cdart, cover, disc, musicbrainz_albumid, musicbrainz_artistid FROM alblist WHERE artist='%s' ORDER BY title ASC''' % artist_name
                    c.execute(query)
            except:
                traceback.print_exc()
        db = c.fetchall()
        c.close()
        for item in db:
            album = {"local_id": (item[0]), "title": xxx_utils.get_unicode(item[1]), "artist": xxx_utils.get_unicode(item[2]), "path": xxx_utils.get_unicode(item[3]).replace('"', ''),
                     "cdart": resources.lib.utils.is_true(xxx_utils.get_unicode(item[4])), "cover": resources.lib.utils.is_true(xxx_utils.get_unicode(item[5])), "disc": (item[6]), "musicbrainz_albumid": xxx_utils.get_unicode(item[7]),
                     "musicbrainz_artistid": xxx_utils.get_unicode(item[8])}
            # print album
            local_album_list.append(album)
    except:
        traceback.print_exc()
        xxx_utils.dialog_msg("close", background=background)
    # log( local_album_list )
    if artist_name == "all artists":
        xxx_utils.dialog_msg("close", background=background)
    settings.log("Finished Retrieving Local Albums from Database")
    return local_album_list


def get_local_artists_db(mode="album_artists", background=False):
    local_artist_list = []
    if mode == "album_artists":
        settings.log("Retrieving Local Album Artists from Database")
        query = '''SELECT DISTINCT local_id, name, musicbrainz_artistid, fanarttv_has_art FROM lalist ORDER BY name ASC'''
    else:
        settings.log("Retrieving All Local Artists from Database")
        query = '''SELECT DISTINCT local_id, name, musicbrainz_artistid, fanarttv_has_art FROM local_artists ORDER BY name ASC'''
    conn_l = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn_l.cursor()
    try:
        c.execute(query)
        db = c.fetchall()
        c.close()
        for item in db:
            artists = {"local_id": (item[0]), "name": xxx_utils.get_unicode(item[1]), "musicbrainz_artistid": xxx_utils.get_unicode(item[2])}
            try:
                if not item[3]:
                    artists["has_art"] = "False"
                else:
                    artists["has_art"] = (item[3])
            except:
                artists["has_art"] = (item[3])
            local_artist_list.append(artists)
    except:
        traceback.print_exc()
    # log( local_artist_list )
    return local_artist_list


def store_local_artist_table(artist_list, background=False):
    count = 0
    percent = 0
    conn = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn.cursor()
    xxx_utils.dialog_msg("create", heading=utils.lang(32124), line1=utils.lang(20186), background=background)
    c.execute('''DROP table IF EXISTS local_artists''')
    c.execute(
        '''CREATE TABLE local_artists(local_id INTEGER, name TEXT, musicbrainz_artistid TEXT, fanarttv_has_art TEXT)''')  # create local artists database
    for artist in artist_list:
        percent = int((count / float(len(artist_list))) * 100)
        xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(32124),
                             line2="%s%s" % (utils.lang(32125), artist["local_id"]),
                             line3="%s%s" % (utils.lang(32028), xxx_utils.get_unicode(artist["name"])), background=background)
        try:
            c.execute(
                '''insert into local_artists(local_id, name, musicbrainz_artistid, fanarttv_has_art) values (?, ?, ?, ?)''',
                (artist["local_id"], xxx_utils.get_unicode(artist["name"]), artist["musicbrainz_artistid"], artist["has_art"]))
            count += 1
        except KeyError:
            c.execute(
                '''insert into local_artists(local_id, name, musicbrainz_artistid, fanarttv_has_art) values (?, ?, ?, ?)''',
                (artist["local_id"], xxx_utils.get_unicode(artist["name"]), artist["musicbrainz_artistid"], "False"))
            count += 1
        except:
            traceback.print_exc()
    conn.commit()
    xxx_utils.dialog_msg("close", background=background)
    c.close()
    return count


def build_local_artist_table(background=False):
    settings.log("Retrieving All Local Artists From XBMC")
    new_local_artist_list = []
    local_artist_list = xxx_jsonrpc_calls.get_all_local_artists()
    local_album_artist_list = get_local_artists_db()
    percent = 1
    count = 1
    total = len(local_artist_list)
    conn = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn.cursor()
    xxx_utils.dialog_msg("create", heading=utils.lang(32124), line1=utils.lang(20186), background=background)
    try:
        for local_artist in local_artist_list:
            if xxx_utils.dialog_msg("iscanceled", background=background):
                break
            artist = {}
            percent = int((count / float(total)) * 100)
            xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(20186),
                                 line2="%s: %s" % (utils.lang(32125), local_artist["artistid"]), line3="%s: %s" % (
                    utils.lang(32137), xxx_utils.get_unicode(artist_list_to_string(local_artist["artist"]))), background=background)
            count += 1
            for album_artist in local_album_artist_list:
                if xxx_utils.dialog_msg("iscanceled", background=background):
                    break
                if local_artist["artistid"] == album_artist["local_id"]:
                    artist["name"] = xxx_utils.get_unicode(artist_list_to_string(local_artist["artist"]))
                    artist["local_id"] = local_artist["artistid"]
                    artist["musicbrainz_artistid"] = album_artist["musicbrainz_artistid"]
                    artist["has_art"] = album_artist["has_art"]
                    break
            if not artist:
                try:
                    artist["name"] = xxx_utils.get_unicode(artist_list_to_string(local_artist["artist"]))
                    name, artist["musicbrainz_artistid"], sort_name = xxx_musicbrainz.get_musicbrainz_artist_id(
                        xxx_utils.get_unicode(artist_list_to_string(local_artist["artist"])))
                except:
                    artist["name"] = xxx_utils.get_unicode(artist_list_to_string(local_artist["artist"]))
                    name, artist["musicbrainz_artistid"], sort_name = xxx_musicbrainz.get_musicbrainz_artist_id(
                        artist_list_to_string(local_artist["artist"]))
                artist["local_id"] = artist_list_to_string(local_artist["artistid"])
                artist["has_art"] = "False"
            new_local_artist_list.append(artist)
        store_local_artist_table(new_local_artist_list, background=background)
        xxx_utils.dialog_msg("close", background=background)
    except:
        settings.log("Problem with making all artists table")
        traceback.print_exc()
        xxx_utils.dialog_msg("close", background=background)
    c.close()
    return count


# retrieves counts for local album, artist and cdarts
def new_local_count():
    settings.log("Counting Local Artists, Albums and cdARTs")
    conn_l = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn_l.cursor()
    try:
        query = "SELECT local_artists, artists, albums, cdarts FROM counts"
        c.execute(query)
        counts = c.fetchall()
        c.close()
        for item in counts:
            local_artist_count = item[0]
            album_artist = item[1]
            album_count = item[2]
            cdart_existing = item[3]
        cdart_existing = recount_cdarts()
        return local_artist_count, album_count, album_artist, cdart_existing
    except UnboundLocalError:
        settings.log("Counts Not Available in Local DB, Rebuilding DB")
        c.close()
        return 0, 0, 0, 0


# # user call from Advanced menu to refresh the addon's database
# def refresh_db(background=False):
#     settings.log("Refreshing Local Database")
#     local_album_count = 0
#     local_artist_count = 0
#     local_cdart_count = 0
#     if xbmcvfs.exists(__settings__.getDatabaseFile()):
#         # File exists needs to be deleted
#         if not background:
#             db_delete = xxx_utils.dialog_msg("yesno", line1=utils.lang(32042), line2=utils.lang(32015), background=background)
#         else:
#             db_delete = True
#         if db_delete:
#             if xbmcvfs.exists(__settings__.getDatabaseFile()):
#                 # backup database
#                 backup_database()
#                 try:
#                     # try to delete exsisting database
#                     xbmcvfs.delete(__settings__.getDatabaseFile())
#                 except:
#                     settings.log("Unable to delete Database")
#             if xbmcvfs.exists(__settings__.getDatabaseFile()):
#                 # if database file still exists even after trying to delete it. Wipe out its contents
#                 conn = sqlite3.connect(__settings__.getDatabaseFile())
#                 c = conn.cursor()
#                 c.execute('''DROP table IF EXISTS counts''')
#                 c.execute('''DROP table IF EXISTS lalist''')  # drop local album artists database
#                 c.execute('''DROP table IF EXISTS alblist''')  # drop local album database
#                 c.execute('''DROP table IF EXISTS unqlist''')  # drop unique database
#                 c.execute('''DROP table IF EXISTS local_artists''')
#                 conn.commit()
#                 c.close()
#             local_album_count, local_artist_count, local_cdart_count = database_setup(background=background)
#         else:
#             pass
#     else:
#         # If file does not exist and some how the program got here, create new database
#         local_album_count, local_artist_count, local_cdart_count = database_setup(background=background)
#     # update counts
#     settings.log("Finished Refeshing Database")
#     return local_album_count, local_artist_count, local_cdart_count


def check_album_mbid(albums, background=False):
    updated_albums = []
    canceled = False
    percent = 1
    count = 0
    if not background:
        xxx_utils.dialog_msg("create", heading=utils.lang(32150))
        xbmc.sleep(500)
    if not albums:
        albums = get_local_albums_db("all artists", background)
    for album in albums:
        update_album = album
        percent = int((count / float(len(albums))) * 100)
        if percent < 1:
            percent = 1
        if percent > 100:
            percent = 100
        count += 1
        if xxx_utils.dialog_msg("iscanceled", background=background):
            canceled = True
            break
        xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(32150),
                             line2="%s: %s" % (utils.lang(32138), xxx_utils.get_unicode(album["title"])),
                             line3="%s: %s" % (utils.lang(32137), xxx_utils.get_unicode(album["artist"])), background=background)
        if album["musicbrainz_albumid"]:
            mbid_match, current_mbid = xxx_musicbrainz.mbid_check(album["musicbrainz_albumid"], "release-group")
            if not mbid_match:
                update_album["musicbrainz_albumid"] = current_mbid
        updated_albums.append(update_album)
    xxx_utils.dialog_msg("close", background=background)
    return updated_albums, canceled


def check_artist_mbid(artists, background=False, mode="all_artists"):
    updated_artists = []
    canceled = False
    percent = 1
    count = 0
    xxx_utils.dialog_msg("create", heading=utils.lang(32149), background=background)
    if not background:
        xbmc.sleep(500)
    if not artists:
        if mode != "all_artists":
            artists = get_local_artists_db("album_artists")
        else:
            artists = get_local_artists_db("all_artists")
    for artist in artists:
        update_artist = artist
        percent = int((count / float(len(artists))) * 100)
        if percent < 1:
            percent = 1
        if percent > 100:
            percent = 100
        count += 1
        if xxx_utils.dialog_msg("iscanceled", background=background):
            canceled = True
            break
        if update_artist["musicbrainz_artistid"]:
            xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(32149),
                                 line2="%s%s" % (utils.lang(32125), update_artist["local_id"]),
                                 line3="%s: %s" % (utils.lang(32137), xxx_utils.get_unicode(update_artist["name"])),
                                 background=background)
            mbid_match, current_mbid = xxx_musicbrainz.mbid_check(update_artist["musicbrainz_artistid"], "artist")
            if not mbid_match:
                update_artist["musicbrainz_artistid"] = current_mbid
        updated_artists.append(update_artist)
    xxx_utils.dialog_msg("close", background=background)
    return updated_artists, canceled


def update_missing_artist_mbid(artists, background=False, mode="all_artists", repair=False):
    if repair:
        settings.log("Updating Removed MBID", xbmc.LOGNOTICE)
    else:
        settings.log("Updating Missing MBID", xbmc.LOGNOTICE)
    updated_artists = []
    canceled = False
    percent = 1
    count = 0
    if not background:
        xxx_utils.dialog_msg("create", heading=utils.lang(32132), background=background)
        xbmc.sleep(500)
    if not artists:
        if mode != "all_artists":
            artists = get_local_artists_db("album_artists")
        else:
            artists = get_local_artists_db("all_artists")
    for artist in artists:
        update_artist = artist
        percent = int((count / float(len(artists))) * 100)
        if percent < 1:
            percent = 1
        if percent > 100:
            percent = 100
        count += 1
        if (len(update_artist["musicbrainz_artistid"]) != 36 and not repair) or (
                        update_artist["musicbrainz_artistid"] == "removed" and repair):
            if xxx_utils.dialog_msg("iscanceled", background=background):
                canceled = True
                break
            xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(32132),
                                 line2="%s%s" % (utils.lang(32125), update_artist["local_id"]),
                                 line3="%s: %s" % (utils.lang(32137), xxx_utils.get_unicode(update_artist["name"])),
                                 background=background)
            try:
                name, update_artist["musicbrainz_artistid"], sort_name = xxx_musicbrainz.get_musicbrainz_artist_id(
                    xxx_utils.get_unicode(update_artist["name"]))
            except:
                name, update_artist["musicbrainz_artistid"], sort_name = xxx_musicbrainz.get_musicbrainz_artist_id(
                    update_artist["name"])
        updated_artists.append(update_artist)
    xxx_utils.dialog_msg("close", background=background)
    return updated_artists, canceled


def update_missing_album_mbid(albums, background=False, repair=False):
    if repair:
        settings.log("Updating Removed MBID", xbmc.LOGNOTICE)
    else:
        settings.log("Updating Missing MBID", xbmc.LOGNOTICE)
    updated_albums = []
    canceled = False
    percent = 1
    count = 0
    if not background:
        xxx_utils.dialog_msg("create", heading=utils.lang(32133))
        xbmc.sleep(500)
    if not albums:
        albums = get_local_albums_db("all artists", background)
    for album in albums:
        update_album = album
        percent = int((count / float(len(albums))) * 100)
        if percent < 1:
            percent = 1
        if percent > 100:
            percent = 100
        count += 1
        if (len(album["musicbrainz_albumid"]) != 36 and not repair) or (
                        album["musicbrainz_albumid"] == "removed" and repair):
            if xxx_utils.dialog_msg("iscanceled", background=background):
                canceled = True
                break
            xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(32133),
                                 line2="%s: %s" % (utils.lang(32138), xxx_utils.get_unicode(album["title"])),
                                 line3="%s: %s" % (utils.lang(32137), xxx_utils.get_unicode(album["artist"])), background=background)
            musicbrainz_albuminfo, discard = xxx_musicbrainz.get_musicbrainz_album(xxx_utils.get_unicode(album["title"]),
                                                                                   xxx_utils.get_unicode(album["artist"]), 0, 1)
            update_album["musicbrainz_albumid"] = musicbrainz_albuminfo["id"]
            update_album["musicbrainz_artistid"] = musicbrainz_albuminfo["artist_id"]
        updated_albums.append(update_album)
    xxx_utils.dialog_msg("close", background=background)
    return updated_albums, canceled


def update_database(background=False):
    settings.log("Updating Addon's DB", xbmc.LOGNOTICE)
    settings.log("Checking to see if DB already exists")
    if not xbmcvfs.exists(__settings__.getDatabaseFile()):
        refresh_db(background)
        return
    if __settings__.getSettingBool("backup_during_update"):
        backup_database()
    update_list = []
    new_list = []
    matched = []
    unmatched = []
    matched_indexed = {}
    album_detail_list_indexed = {}
    local_artists_matched = []
    local_artists_unmatched = []
    local_artists_indexed = {}
    local_artists_matched_indexed = {}
    temp_local_artists = []
    artist = {}
    updated_artists = []
    updated_albums = []
    canceled = False
    local_artist_count = 0
    artist_count = 0
    album_count = 0
    album_artists = get_local_artists_db(mode="album_artists", background=background)
    settings.log("Updating Addon's DB - Checking Albums", xbmc.LOGNOTICE)
    xxx_utils.dialog_msg("create", heading=utils.lang(32134), line1=utils.lang(32105),
                         background=background)  # retrieving all artist from xbmc
    local_album_list = get_local_albums_db("all artists", background)
    xxx_utils.dialog_msg("create", heading=utils.lang(32134), line1=utils.lang(32105),
                         background=background)  # retrieving album list
    album_list = xxx_jsonrpc_calls.retrieve_album_list()
    total = len(album_list)
    xxx_utils.dialog_msg("create", heading=utils.lang(32134), line1=utils.lang(32105),
                         background=background)  # retrieving album details
    album_detail_list = retrieve_album_details_full(album_list, total, background=background, simple=True, update=False)
    xxx_utils.dialog_msg("create", heading=utils.lang(32134), line1=utils.lang(32105),
                         background=background)  # retrieving local artist details
    # album matching
    for item in album_detail_list:
        album_detail_list_indexed[(
            item["disc"], xxx_utils.get_unicode(item["artist"]), xxx_utils.get_unicode(item["title"]), item["cover"], item["cdart"],
            item["local_id"], xxx_utils.get_unicode(item["path"]))] = item
    for item in local_album_list:
        if (item["disc"], xxx_utils.get_unicode(item["artist"]), xxx_utils.get_unicode(item["title"]), item["cover"], item["cdart"],
            item["local_id"], xxx_utils.get_unicode(item["path"])) in album_detail_list_indexed:
            matched.append(item)
    for item in matched:
        matched_indexed[(
            item["disc"], xxx_utils.get_unicode(item["artist"]), xxx_utils.get_unicode(item["title"]), item["cover"], item["cdart"],
            item["local_id"], xxx_utils.get_unicode(item["path"]))] = item
    for item in album_detail_list:
        if not (item["disc"], xxx_utils.get_unicode(item["artist"]), xxx_utils.get_unicode(item["title"]), item["cover"], item["cdart"],
                item["local_id"], xxx_utils.get_unicode(item["path"])) in matched_indexed:
            unmatched.append(item)
    unmatched_details = retrieve_album_details_full(unmatched, len(unmatched), background=background, simple=False,
                                                    update=True)
    combined = matched
    combined.extend(unmatched_details)
    # artist matching
    if __settings__.getExpEnableAllArtits():
        local_artists = xxx_jsonrpc_calls.get_all_local_artists(True)
        settings.log("Updating Addon's DB - Checking Artists", xbmc.LOGNOTICE)
        for artist in local_artists:
            new_artist = {"name": xxx_utils.get_unicode(artist_list_to_string(artist["artist"])), "local_id": artist["artistid"], "musicbrainz_artistid": ""}
            temp_local_artists.append(new_artist)
        local_artists = temp_local_artists
        local_artists_db = get_local_artists_db("all artists")
        for item in local_artists:
            local_artists_indexed[(item["local_id"], xxx_utils.get_unicode(item["name"]))] = item
        for item in local_artists_db:
            if (item["local_id"], xxx_utils.get_unicode(item["name"])) in local_artists_indexed:
                local_artists_matched.append(item)
        for item in local_artists_matched:
            local_artists_matched_indexed[(item["local_id"], xxx_utils.get_unicode(item["name"]))] = item
        for item in local_artists:
            if not (item["local_id"], xxx_utils.get_unicode(item["name"])) in local_artists_matched_indexed:
                local_artists_unmatched.append(item)
        if __settings__.getSettingBool("update_musicbrainz") and not canceled:  # update missing MusicBrainz ID's
            combined_artists, canceled = update_missing_artist_mbid(local_artists_matched, background=background,
                                                                    mode="all_artists")
        else:
            combined_artists = local_artists_matched
        if __settings__.getSettingBool("check_mbid") and not canceled:
            temp_local_artists, canceled = check_artist_mbid(combined_artists, background=background, mode="all_artists")
            combined_artists = temp_local_artists
        if local_artists_unmatched:
            updated_artists, canceled = update_missing_artist_mbid(local_artists_unmatched, background=background, mode="all_artists")
            combined_artists.extend(updated_artists)
    percent = 0
    count = 0
    settings.log("Updating Addon's DB - Getting MusicBrainz ID's for Artist and Albums", xbmc.LOGNOTICE)
    if __settings__.getSettingBool("update_musicbrainz") and not canceled:  # update missing MusicBrainz ID's
        if not canceled:
            updated_albums, canceled = update_missing_album_mbid(combined, background=background)
        combined = updated_albums
    if __settings__.getSettingBool("check_mbid") and not canceled:
        updated_albums, canceled = check_album_mbid(combined, background=background)
        combined = updated_albums
        if __settings__.getExpEnableAllArtits() and not canceled:
            updated_artists, canceled = check_artist_mbid(combined_artists, background=background, mode="all_artists")
            combined_artist = updated_artists
    if canceled:
        xxx_utils.dialog_msg("close", background=background)
        return
    conn = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn.cursor()
    if xbmcvfs.exists(__settings__.getDatabaseFile()):  # if database file still exists even after trying to delete it. Wipe out its contents
        c.execute('''DROP table IF EXISTS lalist_bk''')  # drop the local artists list backup table
        c.execute('''DROP table IF EXISTS local_artists_bk''')  # drop local artists backup table
        c.execute('''CREATE TABLE lalist_bk AS SELECT * FROM lalist''')  # create a backup of the Album artist table
        c.execute(
            '''CREATE TABLE local_artists_bk AS SELECT * FROM local_artists''')  # create a backup of the Local Artist table
        c.execute('''DROP table IF EXISTS counts''')  # drop the count table
        c.execute('''DROP table IF EXISTS lalist''')  # drop local album artists table
        c.execute('''DROP table IF EXISTS alblist''')  # drop local album table
        c.execute('''DROP table IF EXISTS unqlist''')  # drop unique table
        c.execute('''DROP table IF EXISTS local_artists''')
    c.execute(
        '''CREATE TABLE counts(local_artists INTEGER, artists INTEGER, albums INTEGER, cdarts INTEGER, version TEXT)''')
    c.execute(
        '''CREATE TABLE lalist(local_id INTEGER, name TEXT, musicbrainz_artistid TEXT, fanarttv_has_art TEXT)''')  # create local album artists database
    c.execute(
        '''CREATE TABLE alblist(album_id INTEGER, title TEXT, artist TEXT, path TEXT, cdart TEXT, cover TEXT, disc INTEGER, musicbrainz_albumid TEXT, musicbrainz_artistid TEXT)''')  # create local album database
    c.execute(
        '''CREATE TABLE unqlist(title TEXT, disc INTEGER, artist TEXT, path TEXT, cdart TEXT)''')  # create unique database
    c.execute(
        '''CREATE TABLE local_artists(local_id INTEGER, name TEXT, musicbrainz_artistid TEXT, fanarttv_has_art TEXT)''')  # create local artists database
    conn.commit()
    c.close()
    store_counts(0, 0, 0, 0)
    album_count, cdart_existing = store_alblist(combined, background=background)
    album_artist = retrieve_distinct_album_artists()  # then retrieve distinct album artists
    local_artist_list = xxx_jsonrpc_calls.get_all_local_artists(all_artists=False)  # retrieve local artists(to get idArtist)
    local_album_artist_list, artist_count = check_local_albumartist(album_artist, local_artist_list,
                                                                    background=background)
    count = store_lalist(local_album_artist_list, artist_count)  # then store in database
    if __settings__.getExpEnableAllArtits():
        local_artist_count = len(combined_artists)
    store_counts(local_artist_count, artist_count, album_count, cdart_existing)
    if not background:
        xxx_utils.dialog_msg("close", background=background)
        xbmc.sleep(5000)
    if __settings__.getExpEnableAllArtits():
        if len(combined_artists) > 0:
            settings.log("Updating Addon's DB - Adding All Artists to Database", xbmc.LOGNOTICE)
            xxx_utils.dialog_msg("create", heading=utils.lang(32135), background=background)
            store_local_artist_table(combined_artists, background=background)
    conn = sqlite3.connect(__settings__.getDatabaseFile())
    c = conn.cursor()
    # copy fanarttv_has_art values from backup tables if MBIDs match
    c.execute(
        '''UPDATE lalist SET fanarttv_has_art = (SELECT lalist_bk.fanarttv_has_art FROM lalist_bk WHERE lalist_bk.musicbrainz_artistid = lalist.musicbrainz_artistid ) WHERE EXISTS ( SELECT * FROM lalist_bk WHERE lalist_bk.musicbrainz_artistid = lalist.musicbrainz_artistid )''')
    c.execute(
        '''UPDATE local_artists SET fanarttv_has_art = (SELECT local_artists_bk.fanarttv_has_art FROM local_artists_bk WHERE local_artists_bk.musicbrainz_artistid = local_artists.musicbrainz_artistid ) WHERE EXISTS ( SELECT * FROM local_artists_bk WHERE local_artists_bk.musicbrainz_artistid = local_artists.musicbrainz_artistid )''')
    c.execute('''DROP table IF EXISTS lalist_bk''')  # drop local album artists backup table
    c.execute('''DROP table IF EXISTS local_artists_bk''')
    conn.commit()
    c.close()
    restore_user_updates()


def backup_database():
    db_backup_file = __settings__.getDatabaseFileBackupNow()
    if xbmcvfs.exists(db_backup_file):
        try:
            xbmcvfs.delete(db_backup_file)
        except:
            settings.log("Unable to delete Database Backup")
    try:
        xbmcvfs.copy(__settings__.getDatabaseFile(), db_backup_file)
        settings.log("Backing up old Local Database")
    except:
        settings.log("Unable to make Database Backup")
