# -*- coding: utf-8 -*-

import os
import urllib
from traceback import print_exc

import xbmc
import xbmcvfs
import xxx_fanarttv
import xxx_database
import xxx_utils
import resources.lib.utils
import utils
import xxx_jsonrpc_calls

# Helix: PIL is not available in Helix 14.1 on Android
try:
    from PIL import Image
    pil_is_available = True
except:
    pil_is_available = False

import constants
import settings
__settings__ = settings.Settings()


# noinspection PyUnusedLocal
def check_size(path, type_, size_w, size_h):
    # size check is disabled because currently fanart.tv always returns size=1000
    # ref: https://forum.fanart.tv/viewtopic.php?f=4&t=403
    file_name = get_filename(type_, path, "auto")
    source = os.path.join(path, file_name)
    if xbmcvfs.exists(source):
        return False
    else:
        return True

#    # first copy from source to work directory since Python does not support SMB://
#    file_name = get_filename(type, path, "auto")
#    destination = os.path.join(addon_work_folder, "temp", file_name)
#    source = os.path.join(path, file_name)
#    log("Checking Size")
#    if exists(source):
#        file_copy(source, destination)
#    else:
#        return True
#    try:
#        # Helix: PIL is not available in Helix 14.1 on Android
#        if (pil_is_available):
#            # Helix: not really a Helix problem but file cannot be removed after Image.open locking it
#            with open(str(destination), 'rb') as destf:
#                artwork = Image.open(destf)
#            log("Image Size: %s px(W) X %s px(H)" % (artwork.size[0], artwork.size[1]))
#            if artwork.size[0] < size_w and artwork.size[
#                1] < size_h:  # if image is smaller than 1000 x 1000 and the image on fanart.tv = 1000
#                delete_file(destination)
#                log("Image is smaller")
#                return True
#            else:
#                delete_file(destination)
#                log("Image is same size or larger")
#                return False
#        else:
#            log("PIL not available, skipping size check")
#            return False
#    except:
#        log("artwork does not exist. Source: %s" % source)
#        return True


def get_filename(type_, url, mode):
    if type_ == "cdart":
        file_name = "cdart.png"
    elif type_ == "cover":
        file_name = "folder.jpg"
    elif type_ == "fanart":
        if mode == "auto":
            file_name = os.path.basename(url)
        else:
            file_name = "fanart.jpg"
    elif type_ == "clearlogo":
        file_name = "logo.png"
    elif type_ == "artistthumb":
        file_name = "folder.jpg"
    elif type_ == "musicbanner":
        file_name = "banner.jpg"
    else:
        file_name = "unknown"
    return file_name


def make_music_path(artist):
    # Helix: paths MUST end with trailing slash
    path = os.path.join(__settings__.getExpMusicPath(), artist).replace("\\\\", "\\")
    path2 = os.path.join(__settings__.getExpMusicPath(), str.lower(artist)).replace("\\\\", "\\")
    if not xbmcvfs.exists(path2):
        if not xbmcvfs.exists(path):
            if xbmcvfs.mkdirs(path):
                settings.log("Path to music artist made")
                return True
            else:
                settings.log("unable to make path to music artist")
                return False
    else:
        if not xbmcvfs.exists(path):
            if xbmcvfs.mkdirs(path):
                settings.log("Path to music artist made")
                return True
            else:
                settings.log("unable to make path to music artist")
                return False


def download_art(url_cdart, album, database_id, type_, mode, size, background=False):
    settings.log("Downloading artwork... ")
    download_success = False
    percent = 1
    is_canceled = False
    if mode == "auto":
        xxx_utils.dialog_msg("update", percent=percent, background=background)
    else:
        xxx_utils.dialog_msg("create", heading=utils.lang(32047), background=background)
        # Onscreen Dialog - "Downloading...."
    file_name = get_filename(type_, url_cdart, mode)
    # Helix: paths MUST end with trailing slash
    path = os.path.join(album["path"].replace("\\\\", "\\"), '')
    if file_name == "unknown":
        settings.log("Unknown Type ")
        message = [utils.lang(32026), utils.lang(32025), "File: %s" % xxx_utils.get_unicode(path),
                   "Url: %s" % xxx_utils.get_unicode(url_cdart)]
        return message, download_success
    if type_ in ("artistthumb", "cover"):
        thumbnail_path = xxx_jsonrpc_calls.get_thumbnail_path(database_id, type_)
    else:
        thumbnail_path = ""
    if type_ == "fanart" and mode in ("manual", "single"):
        thumbnail_path = xxx_jsonrpc_calls.get_fanart_path(database_id, type_)
    if not xbmcvfs.exists(path):
        try:
            pathsuccess = xbmcvfs.mkdirs(album["path"].replace("\\\\", "\\"))
        except:
            pass
    settings.log("Path: %s" % path)
    settings.log("Filename: %s" % file_name)
    settings.log("url: %s" % url_cdart)

    # cosmetic: use subfolder for downloading instead of work folder
    destination = __settings__.getWorkFile(file_name, constants.WORKDIR_TEMP_GFX)
    final_destination = os.path.join(path, file_name).replace("\\\\", "\\")
    try:
        # this give the ability to use the progress bar by retrieving the downloading information
        # and calculating the percentage
        def _report_hook(count, blocksize, totalsize):
            try:
                percent = int(float(count * blocksize * 100) / totalsize)
                if percent < 1:
                    percent = 1
                if percent > 100:
                    percent = 100
            except:
                percent = 1
            if type_ in ("fanart", "clearlogo", "artistthumb", "musicbanner"):
                xxx_utils.dialog_msg("update", percent=percent,
                                     line1="%s%s" % (utils.lang(32038), xxx_utils.get_unicode(album["artist"])), background=background)
            else:
                xxx_utils.dialog_msg("update", percent=percent,
                                     line1="%s%s" % (utils.lang(32038), xxx_utils.get_unicode(album["artist"])),
                                     line2="%s%s" % (utils.lang(32039), xxx_utils.get_unicode(album["title"])), background=background)
            if mode == "auto":
                if xxx_utils.dialog_msg("iscanceled", background=background):
                    is_canceled = True

        if xbmcvfs.exists(path):
            fp, h = urllib.urlretrieve(url_cdart, destination, _report_hook)
            # message = ["Download Sucessful!"]
            message = [utils.lang(32023), utils.lang(32024), "File: %s" % xxx_utils.get_unicode(path),
                       "Url: %s" % xxx_utils.get_unicode(url_cdart)]
            success = xbmcvfs.copy(destination, final_destination)  # copy it to album folder
            # update database
            try:
                conn = xxx_database.sqlite3.connect(__settings__.getDatabaseFile())
                c = conn.cursor()
                if type_ == "cdart":
                    c.execute('''UPDATE alblist SET cdart="True" WHERE path="%s"''' % (xxx_utils.get_unicode(album["path"])))
                elif type_ == "cover":
                    c.execute('''UPDATE alblist SET cover="True" WHERE path="%s"''' % (xxx_utils.get_unicode(album["path"])))
                conn.commit()
                c.close()
            except:
                settings.log("Error updating database")
                print_exc()
            download_success = True
        else:
            settings.log("Path error")
            settings.log("    file path: %s" % repr(destination))
            message = [utils.lang(32026), utils.lang(32025), "File: %s" % xxx_utils.get_unicode(path),
                       "Url: %s" % xxx_utils.get_unicode(url_cdart)]
            # message = Download Problem, Check file paths - Artwork Not Downloaded]
        # always cleanup downloaded files
        # if type == "fanart":
        xbmcvfs.delete(destination)
    except:
        settings.log("General download error")
        message = [utils.lang(32026), utils.lang(32025), "File: %s" % xxx_utils.get_unicode(path),
                   "Url: %s" % xxx_utils.get_unicode(url_cdart)]
        # message = [Download Problem, Check file paths - Artwork Not Downloaded]
        print_exc()
    if mode == "auto" or mode == "single":
        return message, download_success, final_destination, is_canceled  # returns one of the messages built based on success or lack of
    else:
        xxx_utils.dialog_msg("close", background=background)
        return message, download_success, is_canceled


def cdart_search(cdart_url, id_, disc):
    cdart = {}
    for item in cdart_url:
        if item["musicbrainz_albumid"] == id_ and item["disc"] == disc:
            cdart = item
            break
    return cdart


# Automatic download of non existing cdarts and refreshes addon's db
def auto_download(type_, artist_list, background=False):
    is_canceled = False
    settings.log("Autodownload")
    try:
        artist_count = 0
        download_count = 0
        cdart_existing = 0
        album_count = 0
        d_error = False
        percent = 1
        successfully_downloaded = []
        if type_ in ("clearlogo_allartists", "artistthumb_allartists", "fanart_allartists", "musicbanner_allartists"):
            if type_ == "clearlogo_allartists":
                type_ = "clearlogo"
            elif type_ == "artistthumb_allartists":
                type_ = "artistthumb"
            elif type_ == "musicbanner_allartists":
                type_ = "musicbanner"
            else:
                type_ = "fanart"
        count_artist_local = len(artist_list)
        xxx_utils.dialog_msg("create", heading=utils.lang(32046), background=background)
        # Onscreen Dialog - Automatic Downloading of Artwork
        key_label = type_
        for artist in artist_list:
            low_res = True
            if xxx_utils.dialog_msg("iscanceled", background=background) or is_canceled:
                is_canceled = True
                break
            artist_count += 1
            if not artist["has_art"] == "True":
                # If fanart.tv does not report that it has an artist match skip it.
                continue
            percent = int((artist_count / float(count_artist_local)) * 100)
            if percent < 1:
                percent = 1
            if percent > 100:
                percent = 100
            settings.log("Artist: %-40s Local ID: %-10s   Distant MBID: %s" % (
            artist["name"], artist["local_id"], artist["musicbrainz_artistid"]), xbmc.LOGNOTICE)
            if type_ in ("fanart", "clearlogo", "artistthumb", "musicbanner") and artist["has_art"]:
                xxx_utils.dialog_msg("update", percent=percent, line1="%s%s" % (utils.lang(32038), xxx_utils.get_unicode(artist["name"])),
                                     background=background)
                temp_art = {"musicbrainz_artistid": artist["musicbrainz_artistid"], "artist": artist["name"]}
                auto_art = {"musicbrainz_artistid": artist["musicbrainz_artistid"], "artist": artist["name"]}
                path = os.path.join(__settings__.getExpMusicPath(), resources.lib.utils.sanitize_fs(resources.lib.utils.smart_unicode(artist["name"])))
                if type_ == "fanart":
                    art = xxx_fanarttv.remote_fanart_list(auto_art)
                elif type_ == "clearlogo":
                    art = xxx_fanarttv.remote_clearlogo_list(auto_art)
                    arthd = xxx_fanarttv.remote_hdlogo_list(auto_art)
                elif type_ == "musicbanner":
                    art = xxx_fanarttv.remote_banner_list(auto_art)
                else:
                    art = xxx_fanarttv.remote_artistthumb_list(auto_art)
                if art:
                    if type_ == "fanart":
                        temp_art["path"] = path
                        auto_art["path"] = os.path.join(path, "extrafanart").replace("\\\\", "\\")
                        if not xbmcvfs.exists(auto_art["path"]):
                            try:
                                if xbmcvfs.mkdirs(auto_art["path"]):
                                    settings.log("extrafanart directory made")
                            except:
                                print_exc()
                                settings.log("unable to make extrafanart directory")
                                continue
                        else:
                            settings.log("extrafanart directory already exists")
                    else:
                        auto_art["path"] = path
                    if type_ == "fanart":
                        if __settings__.getSettingBool("enable_fanart_limit"):
                            fanart_dir, fanart_files = xbmcvfs.listdir(auto_art["path"])
                            fanart_number = len(fanart_files)
                            if fanart_number == __settings__.getSettingInt("fanart_limit"):
                                continue
                        if not xbmcvfs.exists(os.path.join(path, "fanart.jpg").replace("\\\\", "\\")):
                            message, d_success, final_destination, is_canceled = download_art(art[0], temp_art,
                                                                                              artist["local_id"],
                                                                                              "fanart", "single", 0,
                                                                                              background)
                        for artwork in art:
                            fanart = {}
                            if __settings__.getSettingBool("enable_fanart_limit") and fanart_number == __settings__.getSettingInt("fanart_limit"):
                                settings.log("Fanart Limit Reached", xbmc.LOGNOTICE)
                                continue
                            if xbmcvfs.exists(os.path.join(auto_art["path"], os.path.basename(artwork))):
                                settings.log("Fanart already exists, skipping")
                                continue
                            else:
                                message, d_success, final_destination, is_canceled = download_art(artwork, auto_art,
                                                                                                  artist["local_id"],
                                                                                                  "fanart", "auto", 0,
                                                                                                  background)
                            if d_success == 1:
                                if __settings__.getSettingBool("enable_fanart_limit"):
                                    fanart_number += 1
                                download_count += 1
                                fanart["artist"] = auto_art["artist"]
                                fanart["path"] = final_destination
                                successfully_downloaded.append(fanart)
                            else:
                                settings.log("Download Error...  Check Path.")
                                settings.log("    Path: %s" % auto_art["path"])
                                d_error = True
                    else:
                        if type_ == "clearlogo":
                            if arthd and __settings__.getSettingBool("enable_hdlogos"):
                                artwork = arthd[0]
                            else:
                                artwork = art[0]
                        else:
                            artwork = art[0]
                        if type_ == "artistthumb":
                            if __settings__.getSettingBool("resizeondownload"):
                                low_res = check_size(auto_art["path"], key_label, 1000, 1000)
                            # Fixed always redownloading Thumbs
                            else:
                                low_res = False
                            if xbmcvfs.exists(os.path.join(auto_art["path"], "folder.jpg")) and not low_res:
                                settings.log("Artist Thumb already exists, skipping")
                                continue
                            else:
                                message, d_success, final_destination, is_canceled = download_art(artwork, auto_art,
                                                                                                  artist["local_id"],
                                                                                                  "artistthumb", "auto",
                                                                                                  0, background)
                        elif type_ == "clearlogo":
                            if __settings__.getSettingBool("enable_hdlogos") and __settings__.getSettingBool("resizeondownload") and arthd:
                                low_res = check_size(auto_art["path"], key_label, 800, 310)
                            else:
                                low_res = False
                            if xbmcvfs.exists(os.path.join(auto_art["path"], "logo.png")) and not low_res:
                                settings.log("ClearLOGO already exists, skipping")
                                continue
                            else:
                                message, d_success, final_destination, is_canceled = download_art(artwork, auto_art,
                                                                                                  artist["local_id"],
                                                                                                  "clearlogo", "auto",
                                                                                                  0, background)
                        elif type_ == "musicbanner":
                            if xbmcvfs.exists(os.path.join(auto_art["path"], "banner.jpg")):
                                settings.log("Music Banner already exists, skipping")
                                continue
                            else:
                                message, d_success, final_destination, is_canceled = download_art(artwork, auto_art,
                                                                                                  artist["local_id"],
                                                                                                  "musicbanner", "auto",
                                                                                                  0, background)
                        if d_success == 1:
                            download_count += 1
                            auto_art["path"] = final_destination
                            successfully_downloaded.append(auto_art)
                        else:
                            settings.log("Download Error...  Check Path.")
                            settings.log("    Path: %s" % auto_art["path"])
                            d_error = True
                else:
                    settings.log("Artist Match not found")
            elif type_ in ("cdart", "cover") and artist["has_art"]:
                local_album_list = xxx_database.get_local_albums_db(artist["name"], background)
                if type_ == "cdart":
                    remote_art_url = xxx_fanarttv.remote_cdart_list(artist)
                else:
                    remote_art_url = xxx_fanarttv.remote_coverart_list(artist)
                for album in local_album_list:
                    low_res = True
                    if xxx_utils.dialog_msg("iscanceled", background=background):
                        break
                    if not remote_art_url:
                        settings.log("No artwork found")
                        break
                    album_count += 1
                    if not album["musicbrainz_albumid"]:
                        continue
                    xxx_utils.dialog_msg("update", percent=percent,
                                         line1="%s%s" % (utils.lang(32038), xxx_utils.get_unicode(artist["name"])),
                                         line2="%s%s" % (utils.lang(32039), xxx_utils.get_unicode(album["title"])), background=background)
                    settings.log("Album: %s" % album["title"])
                    if not album[key_label] or __settings__.getSettingBool("resizeondownload"):
                        musicbrainz_albumid = album["musicbrainz_albumid"]
                        art = xxx_database.artwork_search(remote_art_url, musicbrainz_albumid, album["disc"], key_label)
                        if art:
                            if __settings__.getSettingBool("resizeondownload"):
                                low_res = check_size(album["path"].replace("\\\\", "\\"), key_label, art["size"], art["size"])
                            if art["picture"]:
                                settings.log("ALBUM MATCH ON FANART.TV FOUND")
                                # log( "test_album[0]: %s" % test_album[0] )
                                if low_res:
                                    message, d_success, final_destination, is_canceled = download_art(art["picture"],
                                                                                                      album,
                                                                                                      album["local_id"],
                                                                                                      key_label, "auto",
                                                                                                      0, background)
                                    if d_success == 1:
                                        download_count += 1
                                        album[key_label] = True
                                        album["path"] = final_destination
                                        successfully_downloaded.append(album)
                                    else:
                                        settings.log("Download Error...  Check Path.")
                                        settings.log("    Path: %s" % repr(album["path"]))
                                        d_error = True
                                else:
                                    pass
                            else:
                                settings.log("ALBUM NOT MATCHED ON FANART.TV")
                        else:
                            settings.log("ALBUM NOT MATCHED ON FANART.TV")
                    else:
                        settings.log("%s artwork file already exists, skipping..." % key_label)
        xxx_utils.dialog_msg("close", background=background)
        if d_error:
            xxx_utils.dialog_msg("ok", line1=utils.lang(32026), line2="%s: %s" % (utils.lang(32041), download_count),
                                 background=background)
        else:
            xxx_utils.dialog_msg("ok", line1=utils.lang(32040), line2="%s: %s" % (utils.lang(32041), download_count),
                                 background=background)
        return download_count, successfully_downloaded
    except:
        print_exc()
        xxx_utils.dialog_msg("close", background=background)
