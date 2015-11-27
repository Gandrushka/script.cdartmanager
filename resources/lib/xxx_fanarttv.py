import calendar
from datetime import datetime
from traceback import print_exc

import xbmc
import xbmcvfs

import constants

import xxx_utils
import utils
import xxx_database
import xxx_json_utils

import settings
__settings__ = settings.Settings()

lookup_id = False


def remote_cdart_list(artist_menu):
    settings.log("Finding remote cdARTs")
    cdart_url = []
    try:
        art = retrieve_fanarttv_json(artist_menu["musicbrainz_artistid"])
        if not len(art) < 2:
            album_artwork = art[5]["artwork"]
            if album_artwork:
                for artwork in album_artwork:
                    for cdart in artwork["cdart"]:
                        album = {"artistl_id": artist_menu["local_id"], "artistd_id": artist_menu["musicbrainz_artistid"]}
                        try:
                            album["local_name"] = album["artist"] = artist_menu["name"]
                        except KeyError:
                            album["local_name"] = album["artist"] = artist_menu["artist"]
                        album["musicbrainz_albumid"] = artwork["musicbrainz_albumid"]
                        album["disc"] = cdart["disc"]
                        album["size"] = cdart["size"]
                        album["picture"] = cdart["cdart"]
                        album["thumb_art"] = cdart["cdart"]
                        cdart_url.append(album)
                        # settings.log( "cdart_url: %s " % cdart_url )
    except:
        print_exc()
    return cdart_url


def remote_coverart_list(artist_menu):
    settings.log("Finding remote Cover ARTs")
    coverart_url = []
    try:
        art = retrieve_fanarttv_json(artist_menu["musicbrainz_artistid"])
        if not len(art) < 2:
            album_artwork = art[5]["artwork"]
            if album_artwork:
                for artwork in album_artwork:
                    if artwork["cover"]:
                        album = {"artistl_id": artist_menu["local_id"], "artistd_id": artist_menu["musicbrainz_artistid"], "local_name": artist_menu["name"],
                                 "artist": artist_menu["name"], "musicbrainz_albumid": artwork["musicbrainz_albumid"], "size": 1000, "picture": artwork["cover"],
                                 "thumb_art": artwork["cover"]}
                        coverart_url.append(album)
                        # settings.log( "cdart_url: %s " % cdart_url )
    except:
        print_exc()
    return coverart_url


def remote_fanart_list(artist_menu):
    settings.log("Finding remote fanart")
    backgrounds = ""
    try:
        art = retrieve_fanarttv_json(artist_menu["musicbrainz_artistid"])
        if not len(art) < 3:
            backgrounds = art[0]["backgrounds"]
    except:
        print_exc()
    return backgrounds


def remote_clearlogo_list(artist_menu):
    settings.log("Finding remote clearlogo")
    clearlogo = ""
    try:
        art = retrieve_fanarttv_json(artist_menu["musicbrainz_artistid"])
        if not len(art) < 3:
            clearlogo = art[1]["clearlogo"]
    except:
        print_exc()
    return clearlogo


def remote_hdlogo_list(artist_menu):
    settings.log("Finding remote hdlogo")
    hdlogo = ""
    try:
        art = retrieve_fanarttv_json(artist_menu["musicbrainz_artistid"])
        if not len(art) < 3:
            hdlogo = art[3]["hdlogo"]
    except:
        print_exc()
    return hdlogo


def remote_banner_list(artist_menu):
    settings.log("Finding remote music banners")
    banner = ""
    try:
        art = retrieve_fanarttv_json(artist_menu["musicbrainz_artistid"])
        if not len(art) < 3:
            banner = art[4]["banner"]
    except:
        print_exc()
    return banner


def remote_artistthumb_list(artist_menu):
    settings.log("Finding remote artistthumb")
    artistthumb = ""
    # If there is something in artist_menu["distant_id"] build cdart_url
    try:
        art = retrieve_fanarttv_json(artist_menu["musicbrainz_artistid"])
        if not len(art) < 3:
            artistthumb = art[2]["artistthumb"]
    except:
        print_exc()
    return artistthumb


def retrieve_fanarttv_json(id_):
    settings.log("Retrieving artwork for artist id: %s" % id_)
    # url = music_url_json % (api_key, id, "all")
    url = constants.FANARTTV_MUSIC_BASE_URL % {'mbid': str(id_)}
    # htmlsource = (get_html_source(url, id, save_file=False, overwrite=False)).encode('utf-8', 'ignore')
    htmlsource = xxx_utils.get_html_source(url, "FTV_" + str(id_), save_file=True, overwrite=False)
    artist_artwork = []
    backgrounds = []
    musiclogos = []
    artistthumbs = []
    hdlogos = []
    banners = []
    albums = []
    blank = {}
    fanart = {}
    clearlogo = {}
    artistthumb = {}
    album_art = {}
    hdlogo = {}
    banner = {}
    artist = ""
    artist_id = ""
    IMAGE_TYPES = ['musiclogo',
                   'artistthumb',
                   'artistbackground',
                   'hdmusiclogo',
                   'musicbanner',
                   'albums']
    try:
        data = xxx_json_utils.simplejson.loads(htmlsource)
        # for key, value in data.iteritems():
        for art in IMAGE_TYPES:
            # if value.has_key(art):
            if data.has_key(art):
                # for item in value[art]:
                for item in data[art]:
                    if art == "musiclogo":
                        musiclogos.append(item.get('url'))
                    if art == "hdmusiclogo":
                        hdlogos.append(item.get('url'))
                    if art == "artistbackground":
                        backgrounds.append(item.get('url'))
                    if art == "musicbanner":
                        banners.append(item.get('url'))
                    if art == "artistthumb":
                        artistthumbs.append(item.get('url'))
                    if art == "albums" and not albums:
                        # for album_id in data[artist]["albums"]:
                        for album_id, album in data["albums"].iteritems():
                            album_artwork = {"musicbrainz_albumid": album_id, "cdart": [], "cover": ""}
                            # if value["albums"][album_id].has_key("cdart"):
                            if album.has_key("cdart"):
                                # for item in value["albums"][album_id]["cdart"]:
                                for cditem in album["cdart"]:
                                    cdart = {}
                                    if cditem.has_key("disc"):
                                        cdart["disc"] = int(cditem["disc"])
                                    else:
                                        cdart["disc"] = 1
                                    if cditem.has_key("url"):
                                        cdart["cdart"] = cditem["url"]
                                    else:
                                        cdart["cdart"] = ""
                                    if cditem.has_key("size"):
                                        cdart["size"] = int(cditem["size"])
                                    album_artwork["cdart"].append(cdart)
                            try:
                                if album.has_key("albumcover"):
                                    if len(album["albumcover"]) < 2:
                                        album_artwork["cover"] = album["albumcover"][0]["url"]
                            except:
                                album_artwork["cover"] = ""
                            albums.append(album_artwork)
    except:
        print_exc()
    fanart["backgrounds"] = backgrounds
    clearlogo["clearlogo"] = musiclogos
    hdlogo["hdlogo"] = hdlogos
    banner["banner"] = banners
    artistthumb["artistthumb"] = artistthumbs
    album_art["artwork"] = albums
    artist_artwork.append(fanart)
    artist_artwork.append(clearlogo)
    artist_artwork.append(artistthumb)
    artist_artwork.append(hdlogo)
    artist_artwork.append(banner)
    artist_artwork.append(album_art)
    print artist_artwork
    return artist_artwork


def check_fanart_new_artwork(present_datecode):
    settings.log("Checking for new Artwork on fanart.tv since last run...", xbmc.LOGNOTICE)
    previous_datecode = xxx_database.retrieve_fanarttv_datecode()
    if xbmcvfs.exists(__settings__.getWorkFile("%s.xml" % previous_datecode, constants.WORKDIR_TEMP_XML)):
        xbmcvfs.delete(__settings__.getWorkFile("%s.xml" % previous_datecode, constants.WORKDIR_TEMP_XML))
    url = constants.FANARTTV_MUSIC_LATEST_URL % {'date_code': str(previous_datecode)}
    htmlsource = xxx_utils.get_html_source(url, "FTV-NEW_" + str(present_datecode), save_file=True, overwrite=False)
    if htmlsource == "null":
        settings.log("No new Artwork found on fanart.tv", xbmc.LOGNOTICE)
        return False, htmlsource
    else:
        try:
            settings.log("New Artwork found on fanart.tv", xbmc.LOGNOTICE)
            data = xxx_json_utils.simplejson.loads(htmlsource)
            return True, data
        except:
            htmlsource = "null"
            print_exc()
            return False, htmlsource


def check_art(mbid, artist_type="album"):
    has_art = "False"
    url = constants.FANARTTV_MUSIC_BASE_URL % {'mbid': str(mbid)}
    htmlsource = xxx_utils.get_html_source(url, "FTV_" + str(mbid), save_file=True, overwrite=True)
    if htmlsource == "null":
        settings.log("No artwork found for MBID: %s" % mbid)
        has_art = "False"
    else:
        settings.log("Artwork found for MBID: %s" % mbid)
        has_art = "True"
    return has_art


def update_art(mbid, data, existing_has_art):
    has_art = existing_has_art
    for item in data:
        if item["id"] == mbid:
            url = constants.FANARTTV_MUSIC_BASE_URL % {'mbid': str(mbid)}
            has_art = "True"
            new_art = xxx_utils.get_html_source(url, "FTV_" + str(mbid), save_file=True, overwrite=True)
            break
    return has_art


def first_check(all_artists, album_artists, background=False, update_db=False):
    settings.log("Checking for artist match with fanart.tv - First Check", xbmc.LOGNOTICE)
    heading =utils.lang(32187)
    album_artists_matched = []
    all_artists_matched = []
    d = datetime.utcnow()
    present_datecode = calendar.timegm(d.utctimetuple())
    count = 0
    name = ""
    artist_list = []
    all_artist_list = []
    recognized = []
    recognized_album = []
    fanart_test = ""
    xxx_utils.dialog_msg("create", heading="", background=background)
    for artist in album_artists:
        percent = int((float(count) / len(album_artists)) * 100)
        settings.log("Checking artist MBID: %s" % artist["musicbrainz_artistid"])
        match = {}
        match = artist
        if artist["musicbrainz_artistid"] and (artist["has_art"] == "False" or update_db):
            match["has_art"] = check_art(artist["musicbrainz_artistid"], artist_type="album")
        elif not artist["musicbrainz_artistid"]:
            match["has_art"] = "False"
        else:
            match["has_art"] = artist["has_art"]
        album_artists_matched.append(match)
        xxx_utils.dialog_msg("update", percent=percent, line1=heading, line2="", line3=utils.lang(32049) % artist["name"],
                             background=background)
        count += 1
    settings.log("Storing Album Artists List")
    xxx_database.store_lalist(album_artists_matched, len(album_artists_matched))
    if __settings__.getExpEnableAllArtits() and all_artists:
        count = 0
        for artist in all_artists:
            percent = int((float(count) / len(all_artists)) * 100)
            settings.log("Checking artist MBID: %s" % artist["musicbrainz_artistid"])
            match = {}
            match = artist
            if artist["musicbrainz_artistid"] and (artist["has_art"] == "False" or update_db):
                match["has_art"] = check_art(artist["musicbrainz_artistid"], artist_type="all_artist")
            elif not artist["musicbrainz_artistid"]:
                match["has_art"] = "False"
            else:
                match["has_art"] = artist["has_art"]
            all_artists_matched.append(match)
            xxx_utils.dialog_msg("update", percent=percent, line1=heading, line2="", line3=utils.lang(32049) % artist["name"],
                                 background=background)
            count += 1
        xxx_database.store_local_artist_table(all_artists_matched, background=background)
    xxx_database.store_fanarttv_datecode(present_datecode)
    xxx_utils.dialog_msg("close", background=background)
    settings.log("Finished First Check")
    return


def get_recognized(all_artists, album_artists, background=False):
    settings.log("Checking for artist match with fanart.tv - Get Recognized artists", xbmc.LOGNOTICE)
    album_artists_matched = []
    all_artists_matched = []
    count = 0
    xxx_utils.dialog_msg("create", heading="", background=background)
    present_datecode = calendar.timegm(datetime.utcnow().utctimetuple())
    new_artwork, data = check_fanart_new_artwork(present_datecode)
    if new_artwork:
        for artist in album_artists:
            percent = int((float(count) / len(album_artists)) * 100)
            settings.log("Checking artist MBID: %s" % artist["musicbrainz_artistid"])
            match = artist
            if match["musicbrainz_artistid"]:
                match["has_art"] = update_art(match["musicbrainz_artistid"], data, artist["has_art"])
            album_artists_matched.append(match)
            xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(32185), line2="",
                                 line3=utils.lang(32049) % artist["name"], background=background)
            count += 1
        if __settings__.getExpEnableAllArtits() and all_artists:
            count = 0
            for artist in all_artists:
                percent = int((float(count) / len(all_artists)) * 100)
                settings.log("Checking artist MBID: %s" % artist["musicbrainz_artistid"])
                match = artist
                if match["musicbrainz_artistid"]:
                    match["has_art"] = update_art(match["musicbrainz_artistid"], data, artist["has_art"])
                all_artists_matched.append(match)
                xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(32185), line2="",
                                     line3=utils.lang(32049) % artist["name"], background=background)
                count += 1
    else:
        settings.log("No new music artwork on fanart.tv", xbmc.LOGNOTICE)
        album_artists_matched = album_artists
        all_artists_matched = all_artists
    xxx_database.store_lalist(album_artists_matched, len(album_artists_matched))
    xxx_database.store_local_artist_table(all_artists_matched, background=background)
    xxx_database.store_fanarttv_datecode(present_datecode)
    xxx_utils.dialog_msg("close", background=background)
    settings.log("Finished Getting Recognized Artists")
    return all_artists_matched, album_artists_matched
