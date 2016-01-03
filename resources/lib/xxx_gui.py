# -*- coding: utf-8 -*-
import os
import traceback

import xbmc
import xbmcgui
import xbmcvfs

import constants
import datastore
import settings
import utils
import xxx_database
import xxx_download
import xxx_fanarttv
import xxx_musicbrainz
import xxx_utils

__settings__ = settings.Settings()

kb = xbmc.Keyboard()

KEY_BUTTON_BACK = 275
KEY_KEYBOARD_ESC = 61467


class GUI(xbmcgui.WindowXMLDialog):

    __datastore = None

    def __init__(self, xmlFilename, scriptPath, *args, **kwargs):

        self.menu_mode = 0
        self.artist_menu = {}
        self.remote_cdart_url = []
        self.all_artists = []
        self.local_artists = []
        self.local_albums = []
        self.artwork_type = ""
        self.artists = []
        self.albums = []
        self.album_artists = []
        self.all_artists_list = []
        self.selected_item = 0

        super(GUI, self).__init__(xmlFilename, scriptPath)

    def onInit(self):

        progress = utils.ProgressDialog()
        self.__datastore = datastore.Datastore(progress.artist_album)
        progress.close()

        #  @TODO: translate...
        # albums first, it prefills some artists
        albums_no_mbid = self.__datastore.albums_count_no_mbid()
        if albums_no_mbid > 0 and utils.yesno_dialog("Match albums - powered by TheAudioDB and Musicbrainz",
                                                     "%s of your %s albums do not have a MBID assigned." % (albums_no_mbid, self.__datastore.albums_count()),
                                                     "Should we match them online now?"):
            progress = utils.ProgressDialog()
            self.__datastore.update_datastore("albums", progress.artist_album)
            progress.close()

        #  @TODO: translate...
        artists_no_mbid = self.__datastore.artists_count_no_mbid()
        if artists_no_mbid > 0 and utils.yesno_dialog("Match artists - powered by TheAudioDB and Musicbrainz",
                                                      "%s of your %s artists do not have a MBID assigned." % (artists_no_mbid, self.__datastore.artists_count()),
                                                      "Should we match these artists online now?"):
            progress = utils.ProgressDialog()
            self.__datastore.update_datastore("artists", progress.artist_album)
            progress.close()

        # self.setup_all()

    # sets the colours for the lists
    @staticmethod
    def coloring(text, color, colorword):
        colored_text = text.replace(colorword, "[COLOR=%s]%s[/COLOR]" % (color, colorword))
        return colored_text

    @staticmethod
    def remove_color(text):
        clean_text = text.replace("[/COLOR]", "")
        for k, v in constants.COLORS:
            clean_text = clean_text.replace("[COLOR=%s]" % v, "")
        return clean_text

    # creates the album list on the skin
    def populate_album_list(self, artist_menu, art_url, focus_item, type_):
        settings.log("Populating Album List", xbmc.LOGNOTICE)
        self.getControl(122).reset()
        if not art_url:
            # no cdart found
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            xbmcgui.Window(10001).clearProperty("artwork")
            xxx_utils.dialog_msg("ok", heading=utils.lang(32033), line1=utils.lang(32030), line2=utils.lang(32031))
            # Onscreen Dialog - Not Found on Fanart.tv, Please contribute! Upload your cdARTs, On fanart.tv
            # return
        else:
            local_album_list = xxx_database.get_local_albums_db(art_url[0]["local_name"])
            settings.log("Building album list", xbmc.LOGNOTICE)
            empty_list = False
            check = False
            try:
                for album in local_album_list:
                    if type_ == "cdart":
                        art_image = __settings__.getSkinImage("missing_cdart.png")
                        filename = "cdart.png"
                    else:
                        art_image = __settings__.getSkinImage("missing_cover.png")
                        filename = "folder.jpg"
                    empty_list = False
                    if album["disc"] > 1:
                        label1 = "%s - %s %s" % (album["title"], utils.lang(32016), album["disc"])
                    else:
                        label1 = album["title"]
                    musicbrainz_albumid = album["musicbrainz_albumid"]
                    if not musicbrainz_albumid:
                        empty_list = True
                        continue
                    else:
                        check = True
                    # check to see if there is a thumb
                    artwork = xxx_database.artwork_search(art_url, musicbrainz_albumid, album["disc"], type_)
                    if not artwork:
                        temp_path = os.path.join(album["path"], filename).replace("\\\\", "\\")
                        if xbmcvfs.exists(temp_path):
                            url = art_image = temp_path
                            color = constants.COLORS["orange"]
                        else:
                            url = art_image
                            color = constants.COLORS["white"]
                    else:
                        if artwork["picture"]:
                            # check to see if artwork already exists
                            # set the matched colour local and distant colour
                            # colour the label to the matched colour if not
                            url = artwork["picture"]
                            if album[type_]:
                                art_image = os.path.join(album["path"], filename).replace("\\\\", "\\")
                                color = constants.COLORS["yellow"]
                            else:
                                art_image = url + "/preview"
                                color = constants.COLORS["white"]
                        else:
                            url = ""
                            if album[type_]:
                                art_image = os.path.join(album["path"], filename).replace("\\\\", "\\")
                                color = constants.COLORS["orange"]
                            else:
                                art_image = url
                                color = constants.COLORS["white"]
                    label2 = "%s&&%s&&&&%s&&%s" % (url, album["path"], art_image, str(album["local_id"]))
                    listitem = xbmcgui.ListItem(label=label1, label2=label2, thumbnailImage=art_image)
                    self.getControl(122).addItem(listitem)
                    listitem.setLabel(self.coloring(label1, color, label1))
                    listitem.setLabel2(label2)
                    listitem.setThumbnailImage(art_image)
                    xxx_utils.clear_image_cache(art_image)
            except:
                traceback.print_exc()
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            if (not empty_list) or check:
                self.setFocus(self.getControl(122))
                self.getControl(122).selectItem(focus_item)
            else:
                xbmcgui.Window(10001).clearProperty("artwork")
                xxx_utils.dialog_msg("ok", heading=utils.lang(32033), line1=utils.lang(32030), line2=utils.lang(32031))
                # Onscreen Dialog - Not Found on Fanart.tv, Please contribute! Upload your cdARTs, On fanart.tv
        return

    def populate_album_list_mbid(self, local_album_list, selected_item=0):
        settings.log("MBID Edit - Populating Album List", xbmc.LOGNOTICE)
        if not local_album_list:
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            return
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        try:
            for album in local_album_list:
                label2 = "%s MBID: %s[CR][COLOR=7fffffff]%s MBID: %s[/COLOR]" % (
                    utils.lang(32138), album["musicbrainz_albumid"], utils.lang(32137), album["musicbrainz_artistid"])
                label1 = "%s: %s[CR][COLOR=7fffffff]%s: %s[/COLOR][CR][COLOR=FFE85600]%s[/COLOR]" % (
                    utils.lang(32138), album["title"], utils.lang(32137), album["artist"], album["path"])
                listitem = xbmcgui.ListItem(label=label1, label2=label2)
                self.getControl(145).addItem(listitem)
                listitem.setLabel(label1)
                listitem.setLabel2(label2)
        except:
            traceback.print_exc()
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        self.setFocus(self.getControl(145))
        self.getControl(145).selectItem(selected_item)
        return

    def populate_search_list_mbid(self, mbid_list, type_="artist", selected_item=0):
        settings.log("MBID Search - Populating Search List", xbmc.LOGNOTICE)
        if not mbid_list:
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            return
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        if type_ == "artists":
            try:
                for item in mbid_list:
                    label2 = "MBID: %s" % item["id"]
                    label1 = "%-3s%%: %s" % (item["score"], item["name"])
                    listitem = xbmcgui.ListItem(label=self.coloring(label1, constants.COLORS["white"], label1), label2=label2)
                    self.getControl(161).addItem(listitem)
                    listitem.setLabel(self.coloring(label1, constants.COLORS["white"], label1))
                    listitem.setLabel2(label2)
            except:
                traceback.print_exc()
        elif type_ == "albums":
            try:
                for item in mbid_list:
                    label2 = "%s MBID: %s[CR][COLOR=7fffffff]%s MBID: %s[/COLOR]" % (
                        utils.lang(32138), item["id"], utils.lang(32137), item["artist_id"])
                    label1 = "%-3s%%  %s: %s[CR][COLOR=7fffffff]%s: %s[/COLOR]" % (
                        item["score"], utils.lang(32138), item["title"], utils.lang(32137), item["artist"])
                    listitem = xbmcgui.ListItem(label=label1, label2=label2)
                    self.getControl(161).addItem(listitem)
                    listitem.setLabel(label1)
                    listitem.setLabel2(label2)
            except:
                traceback.print_exc()
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        self.setFocus(self.getControl(161))
        self.getControl(161).selectItem(selected_item)
        return

    def populate_artist_list_mbid(self, local_artist_list, selected_item=0):
        settings.log("MBID Edit - Populating Artist List", xbmc.LOGNOTICE)
        if not local_artist_list:
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            return
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        try:
            for artist in local_artist_list:
                label2 = "MBID: %s" % artist["musicbrainz_artistid"]
                label1 = artist["name"]
                listitem = xbmcgui.ListItem(label=label1, label2=label2)
                self.getControl(145).addItem(listitem)
                listitem.setLabel(label1)
                listitem.setLabel2(label2)
        except:
            traceback.print_exc()
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        self.setFocus(self.getControl(145))
        self.getControl(145).selectItem(selected_item)
        return

    # creates the artist list on the skin
    def populate_artist_list(self, local_artist_list):
        settings.log("Populating Artist List", xbmc.LOGNOTICE)
        if not local_artist_list:
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            return
        try:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            for artist in local_artist_list:
                if artist["has_art"] != "False":
                    listitem = xbmcgui.ListItem(label=self.coloring(artist["name"], "green", artist["name"]))
                    self.getControl(120).addItem(listitem)
                    listitem.setLabel(self.coloring(artist["name"], constants.COLORS["green"], artist["name"]))
                else:
                    listitem = xbmcgui.ListItem(label=artist["name"])
                    self.getControl(120).addItem(listitem)
                    listitem.setLabel(self.coloring(artist["name"],  constants.COLORS["white"], artist["name"]))
        except KeyError:
            for artist in local_artist_list:
                label2 = "MBID: %s" % artist["musicbrainz_artistid"]
                label1 = artist["name"]
                listitem = xbmcgui.ListItem(label=label1, label2=label2)
                self.getControl(120).addItem(listitem)
                listitem.setLabel(label1)
                listitem.setLabel2(label2)
        except:
            traceback.print_exc()
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        self.setFocus(self.getControl(120))
        self.getControl(120).selectItem(0)
        return

    def populate_fanarts(self, artist_menu, focus_item):
        settings.log("Populating Fanart List", xbmc.LOGNOTICE)
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        self.getControl(160).reset()
        try:
            fanart = xxx_fanarttv.remote_fanart_list(artist_menu)
            if fanart:
                for artwork in fanart:
                    # listitem = xbmcgui.ListItem( label = os.path.basename( artwork ), label2 = artist_menu["name"] + "&&&&" + artwork, thumbnailImage = artwork )
                    listitem = xbmcgui.ListItem(label=os.path.basename(artwork),
                                                label2=artist_menu["name"] + "&&&&" + artwork,
                                                thumbnailImage=artwork + "/preview")
                    self.getControl(160).addItem(listitem)
                    listitem.setLabel(os.path.basename(artwork))
                    xbmc.executebuiltin("Dialog.Close(busydialog)")
                    self.setFocus(self.getControl(160))
                    self.getControl(160).selectItem(focus_item)
            else:
                settings.log("[script.cdartmanager - No Fanart for this artist", xbmc.LOGNOTICE)
                xbmc.executebuiltin("Dialog.Close(busydialog)")
                xbmcgui.Window(10001).clearProperty("artwork")
                xxx_utils.dialog_msg("ok", heading=utils.lang(32033), line1=utils.lang(32030), line2=utils.lang(32031))
                # Onscreen Dialog - Not Found on Fanart.tv, Please contribute! Upload your cdARTs, On fanart.tv
                return
        except:
            traceback.print_exc()
            xbmc.executebuiltin("Dialog.Close(busydialog)")

    def populate_musicbanners(self, artist_menu, focus_item):
        settings.log("Populating Music Banner List", xbmc.LOGNOTICE)
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        self.getControl(202).reset()
        try:
            banner = xxx_fanarttv.remote_banner_list(artist_menu)
            if banner:
                for artwork in banner:
                    xxx_utils.clear_image_cache(artwork)
                    listitem = xbmcgui.ListItem(label=os.path.basename(artwork),
                                                label2=artist_menu["name"] + "&&&&" + artwork,
                                                thumbnailImage=artwork + "/preview")
                    # listitem = xbmcgui.ListItem( label = os.path.basename( artwork ), label2 = artist_menu["name"] + "&&&&" + artwork, thumbnailImage = artwork )
                    self.getControl(202).addItem(listitem)
                    listitem.setLabel(os.path.basename(artwork))
                    xbmc.executebuiltin("Dialog.Close(busydialog)")
                    self.setFocus(self.getControl(202))
                    self.getControl(202).selectItem(focus_item)
            else:
                settings.log("[script.cdartmanager - No Music Banners for this artist", xbmc.LOGNOTICE)
                xbmc.executebuiltin("Dialog.Close(busydialog)")
                xbmcgui.Window(10001).clearProperty("artwork")
                xxx_utils.dialog_msg("ok", heading=utils.lang(32033), line1=utils.lang(32030), line2=utils.lang(32031))
                # Onscreen Dialog - Not Found on Fanart.tv, Please contribute! Upload your cdARTs, On fanart.tv
                return
        except:
            traceback.print_exc()
            xbmc.executebuiltin("Dialog.Close(busydialog)")

    def populate_clearlogos(self, artist_menu, focus_item):
        settings.log("Populating ClearLOGO List", xbmc.LOGNOTICE)
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        self.getControl(167).reset()
        hdlogo = ""
        not_found = False
        try:
            clearlogo = xxx_fanarttv.remote_clearlogo_list(artist_menu)
            if __settings__.getSettingBool("enable_hdlogos"):
                hdlogo = xxx_fanarttv.remote_hdlogo_list(artist_menu)
            if clearlogo:
                for artwork in clearlogo:
                    xxx_utils.clear_image_cache(artwork)
                    listitem = xbmcgui.ListItem(label="Standard", label2=artist_menu["name"] + "&&&&" + artwork,
                                                thumbnailImage=artwork + "/preview")
                    self.getControl(167).addItem(listitem)
                    listitem.setLabel(utils.lang(32169))
                    xbmc.executebuiltin("Dialog.Close(busydialog)")
                    self.setFocus(self.getControl(167))
                    self.getControl(167).selectItem(focus_item)
            else:
                not_found = True
            if hdlogo:
                for artwork in hdlogo:
                    xxx_utils.clear_image_cache(artwork)
                    listitem = xbmcgui.listitem = xbmcgui.ListItem(label="HD",
                                                                   label2=artist_menu["name"] + "&&&&" + artwork,
                                                                   thumbnailImage=artwork + "/preview")
                    self.getControl(167).addItem(listitem)
                    listitem.setLabel(utils.lang(32170))
                    xbmc.executebuiltin("Dialog.Close(busydialog)")
                    self.setFocus(self.getControl(167))
                    self.getControl(167).selectItem(focus_item)
            else:
                if not_found:
                    not_found = True
            if not_found:
                settings.log("[script.cdartmanager - No ClearLOGO for this artist", xbmc.LOGNOTICE)
                xbmc.executebuiltin("Dialog.Close(busydialog)")
                xbmcgui.Window(10001).clearProperty("artwork")
                xxx_utils.dialog_msg("ok", heading=utils.lang(32033), line1=utils.lang(32030), line2=utils.lang(32031))
                # Onscreen Dialog - Not Found on Fanart.tv, Please contribute! Upload your cdARTs, On fanart.tv
                return
        except:
            traceback.print_exc()
            xbmc.executebuiltin("Dialog.Close(busydialog)")

    def populate_artistthumbs(self, artist_menu, focus_item):
        settings.log("Populating artist thumb List", xbmc.LOGNOTICE)
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        self.getControl(199).reset()
        try:
            artistthumb = xxx_fanarttv.remote_artistthumb_list(artist_menu)
            if artistthumb:
                for artwork in artistthumb:
                    xxx_utils.clear_image_cache(artwork)
                    listitem = xbmcgui.ListItem(label=os.path.basename(artwork),
                                                label2=artist_menu["name"] + "&&&&" + artwork,
                                                thumbnailImage=artwork + "/preview")
                    self.getControl(199).addItem(listitem)
                    listitem.setLabel(os.path.basename(artwork))
                    xbmc.executebuiltin("Dialog.Close(busydialog)")
                    self.setFocus(self.getControl(199))
                    self.getControl(199).selectItem(focus_item)
            else:
                settings.log("[script.cdartmanager - No artist thumb for this artist", xbmc.LOGNOTICE)
                xbmc.executebuiltin("Dialog.Close(busydialog)")
                xbmcgui.Window(10001).clearProperty("artwork")
                xbmcgui.Dialog().ok(utils.lang(32033), utils.lang(32030), utils.lang(32031))
                # Onscreen Dialog - Not Found on Fanart.tv, Please contribute! Upload your cdARTs, On fanart.tv
                return
        except:
            traceback.print_exc()
            xbmc.executebuiltin("Dialog.Close(busydialog)")

    def populate_downloaded(self, successfully_downloaded, type_):
        settings.log("Populating ClearLOGO List", xbmc.LOGNOTICE)
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        self.getControl(404).reset()
        xbmcgui.Window(10001).setProperty("artwork", type_)
        for item in successfully_downloaded:
            try:
                try:
                    listitem = xbmcgui.ListItem(label=item["artist"], label2=item["title"], thumbnailImage=item["path"])
                except:
                    listitem = xbmcgui.ListItem(label=item["artist"], label2="", thumbnailImage=item["path"])
                self.getControl(404).addItem(listitem)
                listitem.setLabel(item["artist"])
                xbmc.executebuiltin("Dialog.Close(busydialog)")
                self.setFocus(self.getControl(404))
                self.getControl(404).selectItem(0)
            except:
                traceback.print_exc()
                xbmc.executebuiltin("Dialog.Close(busydialog)")

    def populate_local_cdarts(self, focus_item):
        settings.log("Populating Local cdARTS", xbmc.LOGNOTICE)
        url = ""
        work_temp = []
        l_artist = xxx_database.get_local_albums_db("all artists")
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        self.getControl(140).reset()
        for album in l_artist:
            if album["cdart"]:
                cdart_img = os.path.join(album["path"], "cdart.png")
                label2 = "%s&&%s&&&&%s&&%s" % (url, album["path"], cdart_img, album["local_id"])
                label1 = "%s * %s" % (album["artist"], album["title"])
                listitem = xbmcgui.ListItem(label=label1, label2=label2, thumbnailImage=cdart_img)
                self.getControl(140).addItem(listitem)
                listitem.setLabel(self.coloring(label1, constants.COLORS["orange"], label1))
                listitem.setLabel2(label2)
                work_temp.append(album)
            else:
                pass
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        self.setFocus(self.getControl(140))
        self.getControl(140).selectItem(focus_item)
        return work_temp

    @staticmethod
    def single_backup_copy(artist, album, source):
        settings.log("Copying To Backup Folder: %s - %s" % (artist, album), xbmc.LOGNOTICE)
        fn_format = __settings__.getSettingInt("folder")  # int(__addon__.getSetting("folder"))
        backup_folder = __settings__.getSetting("backup_path")
        if not backup_folder:
            __settings__.open()
            backup_folder = __settings__.getSetting("backup_path")
        settings.log("source: %s" % source, xbmc.LOGNOTICE)
        if xbmcvfs.exists(source):
            settings.log("source: %s" % source, xbmc.LOGNOTICE)
            if fn_format == 0:
                destination = os.path.join(backup_folder, (artist.replace("/", "")).replace("'", ""))  # to fix AC/DC
                fn = os.path.join(destination, (((album.replace("/", "")).replace("'", "")) + ".png"))
            else:
                destination = backup_folder
                fn = os.path.join(destination, ((((artist.replace("/", "")).replace("'", "")) + " - " + (
                    (album.replace("/", "")).replace("'", "")) + ".png").lower()))
            settings.log("destination: %s" % destination, xbmc.LOGNOTICE)
            if not xbmcvfs.exists(destination):
                # pass
                xbmcvfs.mkdirs(destination)
            else:
                pass
            settings.log("filename: %s" % fn, xbmc.LOGNOTICE)
            try:
                xbmcvfs.copy(source, fn)
            except:
                settings.log("copying error, check path and file permissions", xbmc.LOGNOTICE)
        else:
            settings.log("Error: cdART file does not exist..  Please check...", xbmc.LOGNOTICE)
        return

    @staticmethod
    def single_cdart_delete(source, album):
        settings.log("Deleting: %s" % source, xbmc.LOGNOTICE)
        conn = xxx_database.sqlite3.connect(__settings__.getDatabaseFile())
        c = conn.cursor()
        cdart = False
        if xbmcvfs.exists(source):
            try:
                xbmcvfs.delete(source)
                c.execute("""UPDATE alblist SET cdart=%s WHERE title='%s'""" % (cdart, album))
                conn.commit()
            except:
                settings.log("Deleteing error, check path and file permissions", xbmc.LOGNOTICE)
        else:
            settings.log("Error: cdART file does not exist..  Please check...", xbmc.LOGNOTICE)
        c.close()
        return

    def restore_from_backup(self):
        settings.log("Restoring cdARTs from backup folder", xbmc.LOGNOTICE)
        xxx_utils.dialog_msg("create", heading=utils.lang(32069))
        # Onscreen Dialog - Restoring cdARTs from backup...
        backup_folder = __settings__.getSetting("backup_path")
        if not backup_folder:
            __settings__.open()
            backup_folder = __settings__.getSetting("backup_path")
        else:
            pass
        self.copy_cdarts(backup_folder)
        xxx_utils.dialog_msg("close")

    def copy_cdarts(self, from_folder):
        settings.log("Copying cdARTs from: %s" % repr(from_folder), xbmc.LOGNOTICE)
        conn = xxx_database.sqlite3.connect(__settings__.getDatabaseFile())
        c = conn.cursor()
        count = 0
        total_count = 0
        fn_format = __settings__.getSettingInt("folder")
        settings.log("Filename format: %s" % fn_format, xbmc.LOGNOTICE)
        settings.log("From Folder: %s" % from_folder, xbmc.LOGNOTICE)
        local_db = xxx_database.get_local_albums_db("all artists")
        total_albums = len(local_db)
        settings.log("total albums: %s" % total_albums, xbmc.LOGNOTICE)
        xxx_utils.dialog_msg("create", heading=utils.lang(32069))
        for album in local_db:
            if xxx_utils.dialog_msg("iscanceled"):
                break
            settings.log("Artist: %-30s  ##  Album: %s" % (repr(album["artist"]), repr(album["title"])), xbmc.LOGNOTICE)
            settings.log("Album Path: %s" % repr(album["path"]), xbmc.LOGNOTICE)
            percent = int(total_count / float(total_albums)) * 100
            if fn_format == 0:
                source = os.path.join(from_folder, (album["artist"].replace("/", "").replace("'",
                                                                                             "")))  # to fix AC/DC and other artists with a / in the name
                if album["disc"] > 1:
                    fn = os.path.join(source, (
                        (album["title"].replace("/", "").replace("'", "")) + "_disc_" + str(album["disc"]) + ".png"))
                else:
                    fn = os.path.join(source, ((album["title"].replace("/", "").replace("'", "")) + ".png"))
                if not xbmcvfs.exists(fn):
                    source = os.path.join(from_folder)
                    if album["disc"] > 1:
                        fn = os.path.join(source, (((album["artist"].replace("/", "").replace("'", "")) + " - " + (
                            album["title"].replace("/", "").replace("'", "")) + "_disc_" + str(
                            album["disc"]) + ".png").lower()))
                    else:
                        fn = os.path.join(source, (((album["artist"].replace("/", "").replace("'", "")) + " - " + (
                            album["title"].replace("/", "").replace("'", "")) + ".png").lower()))
            else:
                source = os.path.join(from_folder)  # to fix AC/DC
                if album["disc"] > 1:
                    fn = os.path.join(source, (((album["artist"].replace("/", "").replace("'", "")) + " - " + (
                        album["title"].replace("/", "").replace("'", "")) + "_disc_" + str(
                        album["disc"]) + ".png").lower()))
                else:
                    fn = os.path.join(source, (((album["artist"].replace("/", "").replace("'", "")) + " - " + (
                        album["title"].replace("/", "").replace("'", "")) + ".png").lower()))
                if not xbmcvfs.exists(fn):
                    source = os.path.join(from_folder, (album["artist"].replace("/", "").replace("'",
                                                                                                 "")))  # to fix AC/DC and other artists with a / in the name
                    fn = os.path.join(source, ((album["title"].replace("/", "").replace("'", "")) + ".png"))
            settings.log("Source folder: %s" % repr(source), xbmc.LOGNOTICE)
            settings.log("Source filename: %s" % repr(fn), xbmc.LOGNOTICE)
            if xbmcvfs.exists(fn):
                destination = os.path.join(album["path"], "cdart.png")
                settings.log("Destination: %s" % repr(destination), xbmc.LOGNOTICE)
                try:
                    xbmcvfs.copy(fn, destination)
                    if from_folder != __settings__.getSetting("backup_path"):
                        xbmcvfs.delete(fn)  # remove file
                    count += 1
                except:
                    settings.log("######  Copying error, check path and file permissions", xbmc.LOGNOTICE)
                try:
                    c.execute("""UPDATE alblist SET cdart="True" WHERE path='%s'""" % album["path"])
                except:
                    settings.log("######  Problem modifying Database!!  Artist: %s   Album: %s" % (
                        repr(album["artist"]), repr(album["title"])), xbmc.LOGNOTICE)
            else:
                pass
            xxx_utils.dialog_msg("update", percent=percent, line1="From Folder: %s" % from_folder,
                                 line2="Filename: %s" % repr(fn), line3="%s: %s" % (utils.lang(32056), count))
            total_count += 1
        xxx_utils.dialog_msg("close")
        conn.commit()
        c.close()
        xxx_utils.dialog_msg("ok", heading=utils.lang(32057), line1="%s %s" % (count, utils.lang(32070)))
        return

        # copy cdarts from music folder to temporary location

    # first step to copy to skin folder
    def cdart_copy(self):
        settings.log("Copying cdARTs to Backup folder", xbmc.LOGNOTICE)
        destination = ""
        duplicates = 0
        percent = 0
        count = 0
        total = 0
        fn_format = __settings__.getSettingInt("folder")
        backup_folder = __settings__.getSetting("backup_path")
        # cdart_list_folder = __addon__.getSetting("cdart_path")
        if not backup_folder:
            __settings__.open()  #__addon__.openSettings()
            backup_folder = __settings__.getSetting("backup_path")
            # cdart_list_folder = __addon__.getSetting("cdart_path")
        albums = xxx_database.get_local_albums_db("all artists")
        xxx_utils.dialog_msg("create", heading=utils.lang(32060))
        for album in albums:
            if xxx_utils.dialog_msg("iscanceled"):
                break
            if album["cdart"]:
                source = os.path.join(album["path"].replace("\\\\", "\\"), "cdart.png")
                settings.log("cdART #: %s" % count, xbmc.LOGNOTICE)
                settings.log("Artist: %-30s  Album: %s" % (repr(album["artist"]), repr(album["title"])), xbmc.LOGNOTICE)
                settings.log("Album Path: %s" % repr(source), xbmc.LOGNOTICE)
                if xbmcvfs.exists(source):
                    if fn_format == 0:
                        destination = os.path.join(backup_folder, (album["artist"].replace("/", "").replace("'", "")))  # to fix AC/DC
                        if album["disc"] > 1:
                            fn = os.path.join(destination, (
                                (album["title"].replace("/", "").replace("'", "")) + "_disc_" + str(album["disc"]) + ".png"))
                        else:
                            fn = os.path.join(destination, ((album["title"].replace("/", "").replace("'", "")) + ".png"))
                    elif fn_format == 1:
                        destination = os.path.join(backup_folder)  # to fix AC/DC
                        if album["disc"] > 1:
                            fn = os.path.join(destination, (
                                (album["artist"].replace("/", "").replace("'", "")) + " - " + (album["title"].replace("/", "").replace("'", "")) + "_disc_" + str(
                                    album["disc"]) + ".png").lower())
                        else:
                            fn = os.path.join(destination, (
                                (album["artist"].replace("/", "").replace("'", "")) + " - " + (
                                    album["title"].replace("/", "").replace("'", "")) + ".png").lower())
                    settings.log("Destination Path: %s" % repr(destination), xbmc.LOGNOTICE)
                    if not xbmcvfs.exists(destination):
                        xbmcvfs.mkdirs(destination)
                    settings.log("Filename: %s" % repr(fn), xbmc.LOGNOTICE)
                    if xbmcvfs.exists(fn):
                        settings.log("################## cdART Not being copied, File exists: %s" % repr(fn), xbmc.LOGNOTICE)
                        duplicates += 1
                    else:
                        try:
                            xbmcvfs.copy(source, fn)
                            count += 1
                            xxx_utils.dialog_msg("update", percent=percent, line1="backup folder: %s" % backup_folder,
                                                 line2="Filename: %s" % repr(fn), line3="%s: %s" % (utils.lang(32056), count))
                        except:
                            settings.log("######  Copying error, check path and file permissions", xbmc.LOGNOTICE)
                else:
                    settings.log("######  Copying error, cdart.png does not exist", xbmc.LOGNOTICE)
            else:
                pass
            percent = int(total / float(len(albums)) * 100)
            total += 1
        xxx_utils.dialog_msg("close")
        settings.log("Duplicate cdARTs: %s" % duplicates, xbmc.LOGNOTICE)
        xxx_utils.dialog_msg("ok", heading=utils.lang(32057), line1="%s: %s" % (utils.lang(32058), backup_folder),
                             line2="%s %s" % (count, utils.lang(32059)), line3="%s Duplicates Found" % duplicates)
        return

    # Search for missing cdARTs and save to missing.txt in Missing List path
    def missing_list(self):
        settings.log("Saving missing.txt file", xbmc.LOGNOTICE)
        count = 0
        percent = 0
        line = ""
        path_provided = False
        albums = xxx_database.get_local_albums_db("all artists")
        artists = xxx_database.get_local_artists_db(mode="local_artists")
        if not artists:
            artists = xxx_database.get_local_artists_db(mode="album_artists")
        xxx_utils.dialog_msg("create", heading=utils.lang(32103), line1=utils.lang(20186), line2="", line3="")
        # temp_destination = os.path.join(addon_work_folder, "missing.txt")
        temp_destination = __settings__.getWorkFile("missing.txt")
        missing_path = __settings__.getSettingPath("missing_path")
        if missing_path:
            final_destination = os.path.join(missing_path, "missing.txt")
            path_provided = True
        else:
            settings.log("Path for missing.txt file not provided", xbmc.LOGNOTICE)
            path_provided = False
        try:
            missing = open(temp_destination, "wb")
            xxx_utils.dialog_msg("update", percent=percent)
            missing.write("Albums Missing Artwork\r\n")
            missing.write("\r")
            missing.write("|  %-45s|  %-75s              |  %-50s|  cdART  |  Cover  |\r\n" % (
                "MusicBrainz ID", "Album Title", "Album Artist"))
            missing.write("-" * 214)
            missing.write("\r\n")
            percent = 1
            for album in albums:
                percent = int((count / float(len(albums))) * 100)
                count += 1
                if percent < 1:
                    percent = 1
                if percent > 100:
                    percent = 100
                if xxx_utils.dialog_msg("iscanceled"):
                    break
                xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(32103),
                                     line2=" %s: %s" % (utils.lang(32039), xxx_utils.get_unicode(album["title"])), line3="")
                cdart = " "
                cover = " "
                if album["cdart"]:
                    cdart = "X"
                if album["cover"]:
                    cover = "X"
                if album["cdart"] and album["cover"]:
                    continue
                else:
                    if int(album["disc"]) > 1:
                        line = "|  %-45s| %-75s     disc#: %2s |  %-50s|    %s    |    %s    |\r\n" % (
                            album["musicbrainz_albumid"], album["title"], album["disc"], album["artist"], cdart, cover)
                    elif int(album["disc"]) == 1:
                        line = "|  %-45s| %-75s               |  %-50s|    %s    |    %s    |\r\n" % (
                            album["musicbrainz_albumid"], album["title"], album["artist"], cdart, cover)
                    else:
                        line = ""
                    if line:
                        try:
                            missing.write(line.encode("utf8"))
                        except:
                            missing.write(repr(line))
                        missing.write("-" * 214)
                        missing.write("\r\n")
            missing.write("\r\n")
            xxx_utils.dialog_msg("update", percent=50)
            missing.write("Artists Missing Artwork\r\n")
            missing.write("\r\n")
            music_path = __settings__.getExpMusicPath()
            missing.write("|  %-45s| %-70s| Fanart | clearLogo | Artist Thumb | Music Banner |\r\n" % (
                "MusicBrainz ID", "Artist Name"))
            missing.write("-" * 172)
            missing.write("\r\n")
            count = 0
            percent = 1
            for artist in artists:
                count += 1
                percent = int((count / float(len(artists))) * 100)
                if percent < 1:
                    percent = 1
                if percent > 100:
                    percent = 100
                if xxx_utils.dialog_msg("iscanceled"):
                    break
                xxx_utils.dialog_msg("update", percent=percent, line1=utils.lang(32103),
                                     line2=" %s: %s" % (utils.lang(32038), xxx_utils.get_unicode(artist["name"])), line3="")
                fanart = " "
                clearlogo = " "
                artistthumb = " "
                musicbanner = " "
                line = ""
                fanart_path = os.path.join(music_path, artist["name"], "fanart.jpg").replace("\\\\", "\\")
                clearlogo_path = os.path.join(music_path, artist["name"], "logo.png").replace("\\\\", "\\")
                artistthumb_path = os.path.join(music_path, artist["name"], "folder.jpg").replace("\\\\", "\\")
                musicbanner_path = os.path.join(music_path, artist["name"], "banner.jpg").replace("\\\\", "\\")
                if xbmcvfs.exists(fanart_path):
                    fanart = "X"
                if xbmcvfs.exists(clearlogo_path):
                    clearlogo = "X"
                if xbmcvfs.exists(artistthumb_path):
                    artistthumb = "X"
                if xbmcvfs.exists(musicbanner_path):
                    musicbanner = "X"
                if not xbmcvfs.exists(fanart_path) or not xbmcvfs.exists(clearlogo_path) or not xbmcvfs.exists(
                        artistthumb_path) or not xbmcvfs.exists(musicbanner_path):
                    line = "|  %-45s| %-70s|    %s   |    %s      |      %s       |      %s       |\r\n" % (
                        artist["musicbrainz_artistid"], artist["name"], fanart, clearlogo, artistthumb, musicbanner)
                if line:
                    try:
                        missing.write(line.encode("utf8"))
                    except:
                        missing.write(repr(line))
                    missing.write("-" * 172)
                    missing.write("\r\n")
            missing.close()
        except:
            settings.log("Error saving missing.txt file", xbmc.LOGNOTICE)
            traceback.print_exc()
        if xbmcvfs.exists(temp_destination) and path_provided:
            xbmcvfs.copy(temp_destination, final_destination)
        xxx_utils.dialog_msg("close")

    def refresh_counts(self, local_album_count, local_artist_count, local_cdart_count):
        settings.log("Refreshing Counts", xbmc.LOGNOTICE)
        self.getControl(109).setLabel(utils.lang(32500) % local_artist_count)
        self.getControl(110).setLabel(utils.lang(32010) % local_album_count)
        self.getControl(112).setLabel(utils.lang(32008) % local_cdart_count)

    # This selects which cdART image shows up in the display box (image id 210) 
    def cdart_icon(self):
        cdart_path = {}
        try:  # If there is information in label 2 of list id 140(local album list)
            local_cdart = (self.getControl(140).getSelectedItem().getLabel2()).split("&&&&")[1]
            url = ((self.getControl(140).getSelectedItem().getLabel2()).split("&&&&")[0]).split("&&")[1]
            cdart_path["path"] = ((self.getControl(140).getSelectedItem().getLabel2()).split("&&&&")[0]).split("&&")[0]
            settings.log("# cdART url: %s" % url, xbmc.LOGNOTICE)
            settings.log("# cdART path: %s" % cdart_path["path"], xbmc.LOGNOTICE)
            if local_cdart:  # Test to see if there is a path in local_cdart
                image = (local_cdart.replace("\\\\", "\\"))
                self.getControl(210).setImage(image)
            else:
                if cdart_path["path"]:  # Test to see if there is an url in cdart_path["path"]
                    image = (cdart_path["path"].replace("\\\\", "\\"))
                    self.getControl(210).setImage(image)
                else:
                    image = ""
                    # image = image
        except:  # If there is not any information in any of those locations, no image.
            traceback.print_exc()
            image = __settings__.getSkinImage("blank_artwork.png")
        self.getControl(210).setImage(image)

    def clear_artwork(self):
        self.getControl(211).setImage(__settings__.getIcon())
        self.getControl(210).setImage(__settings__.getIcon())

    @staticmethod
    def popup(header, line1, line2, line3):
        xxx_utils.dialog_msg("create", heading=header, line1=line1, line2=line2, line3=line3)
        xbmc.sleep(2000)
        xxx_utils.dialog_msg("close")

    def get_mbid_keyboard(self, type_="artist"):
        mbid = "canceled"
        if type_ == "artist":
            kb.setHeading(utils.lang(32159))
            # default_text = self.artist_menu["musicbrainz_artistid"]
        elif type_ == "albumartist":
            kb.setHeading(utils.lang(32159))
            # default_text = self.album_menu["musicbrainz_artistid"]
        elif type_ == "album":
            kb.setHeading(utils.lang(32166))
            # default_text = self.album_menu["musicbrainz_albumid"]
        # try:
        #    kb.setDefault( default_text )
        # except:
        #    kb.setDefault( repr( default_text ) )
        kb.doModal()
        while 1:
            if not (kb.isConfirmed()):
                canceled = True
                break
            else:
                mbid = kb.getText()
                if type_ == "artist":
                    if len(mbid) == 0 and len(self.artist_menu["musicbrainz_artistid"]) != 0:
                        if xxx_utils.dialog_msg("yesno", heading=utils.lang(32163),
                                                line1=self.artist_menu["musicbrainz_artistid"]):
                            canceled = False
                            break
                elif type_ == "albumartist":
                    if len(mbid) == 0 and len(self.artist_menu["musicbrainz_artistid"]) != 0:
                        if xxx_utils.dialog_msg("yesno", heading=utils.lang(32163),
                                                line1=self.album_menu["musicbrainz_artistid"]):
                            canceled = False
                            break
                elif type_ == "album":
                    if len(mbid) == 0 and len(self.artist_menu["musicbrainz_albumid"]) != 0:
                        if xxx_utils.dialog_msg("yesno", heading=utils.lang(32163),
                                                line1=self.album_menu["musicbrainz_albumid"]):
                            canceled = False
                            break
                if len(mbid) == 36:
                    if xxx_utils.dialog_msg("yesno", heading=utils.lang(32162), line1=mbid):
                        canceled = False
                        break
                    else:
                        mbid = "canceled"
                        kb.doModal()
                        continue
                if len(mbid) == 32:  # user did not enter dashes
                    temp_mbid = list(mbid)
                    temp_mbid.insert(8, "-")
                    temp_mbid.insert(13, "-")
                    temp_mbid.insert(18, "-")
                    temp_mbid.insert(23, "-")
                    mbid = "".join(temp_mbid)
                else:
                    mbid = "canceled"
                    if xxx_utils.dialog_msg("yesno", heading=utils.lang(32160), line1=utils.lang(32161)):
                        kb.doModal()
                        continue
                    else:
                        canceled = True
                        break
        return mbid, canceled

    # # setup self. strings and initial local counts
    # def setup_all(self):
    #     settings.log("# Setting up Script", xbmc.LOGNOTICE)
    #     # checking to see if addon_db exists, if not, run database_setup()
    #     if xbmcvfs.exists(__settings__.getDatabaseFile()):
    #         settings.log("Addon Db found - Loading Counts", xbmc.LOGNOTICE)
    #         all_artist_count, local_album_count, local_artist_count, local_cdart_count = xxx_database.new_local_count()
    #     else:
    #         settings.log("Addon Db Not Found - Building New Addon Db", xbmc.LOGNOTICE)
    #         local_album_count, local_artist_count, local_cdart_count = xxx_database.database_setup(self.background)
    #         self.local_artists = xxx_database.get_local_artists_db()  # retrieve data from addon's database
    #         self.setFocusId(100)  # set menu selection to the first option(cdARTs)
    #         local_artists = xxx_database.get_local_artists_db(mode="album_artists")
    #         if __settings__.getExpEnableAllArtits():
    #             all_artists = xxx_database.get_local_artists_db(mode="all_artists")
    #         else:
    #             all_artists = []
    #         xxx_fanarttv.first_check(all_artists, local_artists)
    #     self.refresh_counts(local_album_count, local_artist_count, local_cdart_count)
    #     self.local_artists = xxx_database.get_local_artists_db()  # retrieve data from addon's database
    #     self.setFocusId(100)  # set menu selection to the first option(cdARTs)
    #     album_artists = xxx_database.get_local_artists_db(mode="album_artists")
    #     if __settings__.getExpEnableAllArtits():
    #         all_artists = xxx_database.get_local_artists_db(mode="all_artists")
    #     else:
    #         all_artists = []
    #     present_datecode = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
    #     new_artwork, data = xxx_fanarttv.check_fanart_new_artwork(present_datecode)
    #     if new_artwork:
    #         self.all_artists_list, self.album_artists = xxx_fanarttv.get_recognized(all_artists, album_artists)
    #     else:
    #         self.all_artists_list = all_artists
    #         self.album_artists = album_artists

    def onClick(self, controlId):
        # print controlId
        empty = []
        if controlId in (105, 150):  # cdARTs Search Artists
            if controlId == 105:
                self.menu_mode = 1
                self.artwork_type = "cdart"
            elif controlId == 150:
                self.menu_mode = 3
                self.artwork_type = "cover"
            self.local_artists = self.album_artists
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            self.getControl(120).reset()
            self.getControl(140).reset()
            self.populate_artist_list(self.album_artists)
        if controlId == 120:  # Retrieving information from Artists List
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            # self.clear_artwork()
            self.artist_menu = {"local_id": (self.local_artists[self.getControl(120).getSelectedPosition()]["local_id"]), "name": xxx_utils.get_unicode(
                self.local_artists[self.getControl(120).getSelectedPosition()]["name"]), "musicbrainz_artistid": xxx_utils.get_unicode(
                self.local_artists[self.getControl(120).getSelectedPosition()]["musicbrainz_artistid"])}
            if not self.menu_mode in (10, 11, 12, 14):
                self.artist_menu["has_art"] = self.local_artists[self.getControl(120).getSelectedPosition()]["has_art"]
                if not self.artist_menu["musicbrainz_artistid"]:
                    self.artist_menu["musicbrainz_artistid"] = xxx_musicbrainz.update_musicbrainzid("artist", self.artist_menu)
            artist_name = xxx_utils.get_unicode(self.artist_menu["name"])
            self.getControl(204).setLabel(utils.lang(32038) + "[CR]%s" % artist_name)
            if self.menu_mode == 1:
                self.remote_cdart_url = xxx_fanarttv.remote_cdart_list(self.artist_menu)
                xbmcgui.Window(10001).setProperty("artwork", "cdart")
                self.populate_album_list(self.artist_menu, self.remote_cdart_url, 0, "cdart")
            elif self.menu_mode == 3:
                self.remote_cdart_url = xxx_fanarttv.remote_coverart_list(self.artist_menu)
                xbmcgui.Window(10001).setProperty("artwork", "cover")
                self.populate_album_list(self.artist_menu, self.remote_cdart_url, 0, "cover")
            elif self.menu_mode == 6:
                xbmcgui.Window(10001).setProperty("artwork", "fanart")
                self.populate_fanarts(self.artist_menu, 0)
            elif self.menu_mode == 7:
                xbmcgui.Window(10001).setProperty("artwork", "clearlogo")
                self.populate_clearlogos(self.artist_menu, 0)
            elif self.menu_mode == 9:
                xbmcgui.Window(10001).setProperty("artwork", "artistthumb")
                self.populate_artistthumbs(self.artist_menu, 0)
            elif self.menu_mode == 11:
                self.local_albums = xxx_database.get_local_albums_db(self.artist_menu["name"])
                self.getControl(145).reset()
                self.populate_album_list_mbid(self.local_albums)
            elif self.menu_mode == 13:
                xbmcgui.Window(10001).setProperty("artwork", "musicbanner")
                self.populate_musicbanners(self.artist_menu, 0)

        if controlId == 145:
            self.selected_item = self.getControl(145).getSelectedPosition()
            if self.menu_mode == 10:  # Artist
                self.artist_menu = {"local_id": (
                    self.local_artists[self.getControl(145).getSelectedPosition()]["local_id"]), "name": xxx_utils.get_unicode(
                    self.local_artists[self.getControl(145).getSelectedPosition()]["name"]), "musicbrainz_artistid": xxx_utils.get_unicode(
                    self.local_artists[self.getControl(145).getSelectedPosition()]["musicbrainz_artistid"])}
                self.setFocusId(157)
                try:
                    self.getControl(156).setLabel(
                        utils.lang(32038) + "[CR]%s" % xxx_utils.get_unicode(self.artist_menu["name"]))
                except:
                    self.getControl(156).setLabel(utils.lang(32038) + "[CR]%s" % repr(self.artist_menu["name"]))
            if self.menu_mode in (11, 12):  # Album
                self.album_menu = {"local_id": (
                    self.local_albums[self.getControl(145).getSelectedPosition()]["local_id"]), "title": xxx_utils.get_unicode(
                    self.local_albums[self.getControl(145).getSelectedPosition()]["title"]), "musicbrainz_albumid": xxx_utils.get_unicode(
                    self.local_albums[self.getControl(145).getSelectedPosition()]["musicbrainz_albumid"]), "artist": xxx_utils.get_unicode(
                    self.local_albums[self.getControl(145).getSelectedPosition()]["artist"]), "path": xxx_utils.get_unicode(
                    self.local_albums[self.getControl(145).getSelectedPosition()]["path"]), "musicbrainz_artistid": xxx_utils.get_unicode(
                    self.local_albums[self.getControl(145).getSelectedPosition()]["musicbrainz_artistid"])}
                self.setFocusId(157)
                try:
                    self.getControl(156).setLabel(
                        utils.lang(32039) + "[CR]%s" % xxx_utils.get_unicode(self.album_menu["title"]))
                except:
                    self.getControl(156).setLabel(utils.lang(32039) + "[CR]%s" % repr(self.album_menu["title"]))

        if controlId == 157:  # Manual Edit
            canceled = False
            if self.menu_mode == 10:  # Artist
                conn = xxx_database.sqlite3.connect(__settings__.getDatabaseFile())
                c = conn.cursor()
                xbmc.executebuiltin("Dialog.Close(busydialog)")
                mbid, canceled = self.get_mbid_keyboard("artist")
                if not canceled:
                    try:
                        c.execute('''UPDATE lalist SET musicbrainz_artistid="%s" WHERE local_id=%s''' % (
                            mbid, self.artist_menu["local_id"]))
                    except:
                        settings.log("Error updating database(lalist)", xbmc.LOGERROR)
                        traceback.print_exc()
                    try:
                        c.execute('''UPDATE alblist SET musicbrainz_artistid="%s" WHERE musicbrainz_artistid="%s"''' % (
                            mbid, self.artist_menu["musicbrainz_artistid"]))
                    except:
                        settings.log("Error updating database(lalist)", xbmc.LOGERROR)
                        traceback.print_exc()
                    try:
                        c.execute('''UPDATE local_artists SET musicbrainz_artistid="%s" WHERE local_id=%s''' % (
                            mbid, self.artist_menu["local_id"]))
                    except:
                        settings.log("Error updating database(local_artists)", xbmc.LOGERROR)
                        traceback.print_exc()
                    conn.commit()
                c.close()
            if self.menu_mode == 11:  # album
                conn = xxx_database.sqlite3.connect(__settings__.getDatabaseFile())
                c = conn.cursor()
                xbmc.executebuiltin("Dialog.Close(busydialog)")
                artist_mbid, canceled = self.get_mbid_keyboard("albumartist")
                if not canceled:
                    album_mbid, canceled = self.get_mbid_keyboard("album")
                    if not canceled:
                        try:
                            c.execute(
                                '''UPDATE alblist SET musicbrainz_albumid="%s", musicbrainz_artistid="%s" WHERE album_id=%s and path="%s"''' % (
                                    album_mbid, artist_mbid, self.album_menu["local_id"], self.album_menu["path"]))
                        except:
                            settings.log("Error updating database(alblist)", xbmc.LOGERROR)
                            traceback.print_exc()
                        try:
                            c.execute('''UPDATE lalist SET musicbrainz_artistid="%s" WHERE local_id=%s''' % (
                                mbid, self.album_menu["local_id"]))
                        except:
                            settings.log("Error updating database(lalist)", xbmc.LOGERROR)
                            traceback.print_exc()
                        try:
                            c.execute('''UPDATE local_artists SET musicbrainz_artistid="%s" WHERE local_id=%s''' % (
                                mbid, self.album_menu["local_id"]))
                        except:
                            settings.log("Error updating database(local_artists)", xbmc.LOGERROR)
                            traceback.print_exc()
                        conn.commit()
                c.close()
            local_artists = xxx_database.get_local_artists_db(mode="album_artists")
            if __settings__.getExpEnableAllArtits():
                all_artists = xxx_database.get_local_artists_db(mode="all_artists")
            else:
                all_artists = []
            self.all_artists_list, self.album_artists = xxx_fanarttv.get_recognized(all_artists, local_artists)
            if self.menu_mode == 11:
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                self.getControl(145).reset()
                self.local_albums = xxx_database.get_local_albums_db(self.album_menu["artist"])
                self.populate_album_list_mbid(self.local_albums, self.selected_item)
            elif self.menu_mode == 10:
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                self.getControl(145).reset()
                if __settings__.getExpEnableAllArtits():
                    self.local_artists = all_artists
                else:
                    self.local_artists = local_artists
                self.populate_artist_list_mbid(self.local_artists)

        if controlId == 122:  # Retrieving information from Album List
            self.getControl(140).reset()
            select = None
            local = ""
            url = ""
            album = {}
            album_search = []
            album_selection = []
            cdart_path = {}
            local_cdart = ""
            count = 0
            select = 0
            local_cdart = ((self.getControl(122).getSelectedItem().getLabel2()).split("&&&&")[1]).split("&&")[0]
            database_id = int(((self.getControl(122).getSelectedItem().getLabel2()).split("&&&&")[1]).split("&&")[1])
            url = ((self.getControl(122).getSelectedItem().getLabel2()).split("&&&&")[0]).split("&&")[0]
            cdart_path["path"] = ((self.getControl(122).getSelectedItem().getLabel2()).split("&&&&")[0]).split("&&")[1]
            try:
                cdart_path["artist"] = xxx_utils.get_unicode(self.getControl(204).getLabel()).replace(
                    utils.lang(32038) + "[CR]", "")
            except:
                cdart_path["artist"] = repr(self.getControl(204).getLabel()).replace(utils.lang(32038) + "[CR]", "")
            cdart_path["title"] = self.getControl(122).getSelectedItem().getLabel()
            cdart_path["title"] = self.remove_color(cdart_path["title"])
            self.selected_item = self.getControl(122).getSelectedPosition()
            if not url == "":  # If it is a recognized Album...
                if self.menu_mode == 1:
                    message, d_success, is_canceled = xxx_download.download_art(url, cdart_path, database_id, "cdart", "manual", 0)
                elif self.menu_mode == 3:
                    message, d_success, is_canceled = xxx_download.download_art(url, cdart_path, database_id, "cover", "manual", 0)
                xxx_utils.dialog_msg("close")
                xxx_utils.dialog_msg("ok", heading=message[0], line1=message[1], line2=message[2], line3=message[3])
            else:  # If it is not a recognized Album...
                settings.log("Oops --  Some how I got here... - ControlID(122)", xbmc.LOGDEBUG)
            all_artist_count, local_album_count, local_artist_count, local_cdart_count = xxx_database.new_local_count()
            self.refresh_counts(local_album_count, local_artist_count, local_cdart_count)
            artist_name = xxx_utils.get_unicode(self.artist_menu["name"])
            self.getControl(204).setLabel(utils.lang(32038) + "[CR]%s" % artist_name)
            if self.menu_mode == 1:
                self.remote_cdart_url = xxx_fanarttv.remote_cdart_list(self.artist_menu)
                xbmcgui.Window(10001).setProperty("artwork", "cdart")
                self.populate_album_list(self.artist_menu, self.remote_cdart_url, self.selected_item, "cdart")
            elif self.menu_mode == 3:
                self.remote_cdart_url = xxx_fanarttv.remote_coverart_list(self.artist_menu)
                xbmcgui.Window(10001).setProperty("artwork", "cover")
                self.populate_album_list(self.artist_menu, self.remote_cdart_url, self.selected_item, "cover")

        if controlId == 132:  # Clean Music database selected from Advanced Menu
            settings.log("#  Executing Built-in - CleanLibrary(music)", xbmc.LOGNOTICE)
            xbmc.executebuiltin("CleanLibrary(music)")

        if controlId == 133:  # Update Music database selected from Advanced Menu
            settings.log("#  Executing Built-in - UpdateLibrary(music)", xbmc.LOGNOTICE)
            xbmc.executebuiltin("UpdateLibrary(music)")

        if controlId == 135:  # Back up cdART selected from Advanced Menu
            self.cdart_copy()

        if controlId == 134:
            settings.log("No function here anymore", xbmc.LOGNOTICE)

        if controlId == 131:  # Modify Local Database
            self.setFocusId(190)  # change when other options

        if controlId == 190:  # backup database
            xxx_database.backup_database()
            xbmc.executebuiltin(
                "Notification( %s, %s, %d, %s)" % (utils.lang(32042), utils.lang(32139), 2000, __settings__.getIcon()))

        if controlId == 191:  # Refresh Local database selected from Advanced Menu
            xxx_database.refresh_db(False)
            xxx_utils.dialog_msg("close")
            local_artists = xxx_database.get_local_artists_db(mode="album_artists")
            if __settings__.getExpEnableAllArtits():
                all_artists = xxx_database.get_local_artists_db(mode="all_artists")
            else:
                all_artists = []
            self.all_artists_list, self.album_artists = xxx_fanarttv.get_recognized(all_artists, local_artists)
            all_artist_count, local_album_count, local_artist_count, local_cdart_count = xxx_database.new_local_count()
            self.refresh_counts(local_album_count, local_artist_count, local_cdart_count)

        # if controlId == 192:  # Update database
        #     xxx_database.update_database(False)
        #     xxx_utils.dialog_msg("close")
        #     local_artists = xxx_database.get_local_artists_db(mode="album_artists")
        #     if __settings__.getExpEnableAllArtits():
        #         all_artists = xxx_database.get_local_artists_db(mode="all_artists")
        #     else:
        #         all_artists = []
        #     xxx_fanarttv.first_check(all_artists, local_artists, background=False, update_db=True)
        #     self.all_artists_list, self.album_artists = xxx_fanarttv.get_recognized(all_artists, local_artists)
        #     all_artist_count, local_album_count, local_artist_count, local_cdart_count = xxx_database.new_local_count()
        #     self.refresh_counts(local_album_count, local_artist_count, local_cdart_count)

        if controlId == 136:  # Restore from Backup
            self.restore_from_backup()
            all_artist_count, local_album_count, local_artist_count, local_cdart_count = xxx_database.new_local_count()
            self.refresh_counts(local_album_count, local_artist_count, local_cdart_count)

        if controlId == 137:  # Local cdART List
            self.getControl(122).reset()
            self.menu_mode = 8
            xbmcgui.Window(10001).setProperty("artwork", "cdart")
            self.populate_local_cdarts(0)

        if controlId == 107:
            self.setFocusId(200)

        if controlId == 108:
            self.setFocusId(200)

        if controlId == 130:  # cdART Backup Menu
            self.setFocusId(135)

        if controlId == 140:  # Local cdART selection
            self.cdart_icon()
            self.setFocusId(142)
            artist_album = self.getControl(140).getSelectedItem().getLabel()
            artist_album = self.remove_color(artist_album)
            artist = artist_album.split(" * ")[0]
            album_title = artist_album.split(" * ")[1]
            self.getControl(301).setLabel(self.getControl(140).getSelectedItem().getLabel())

        if controlId in (142, 143):  # , 144):
            path = ((self.getControl(140).getSelectedItem().getLabel2()).split("&&&&")[1]).split("&&")[0]
            database_id = int(((self.getControl(140).getSelectedItem().getLabel2()).split("&&&&")[1]).split("&&")[1])
            artist_album = self.getControl(140).getSelectedItem().getLabel()
            artist_album = self.remove_color(artist_album)
            artist = artist_album.split(" * ")[0]
            album_title = artist_album.split(" * ")[1]
            if controlId == 143:  # Delete cdART
                self.single_cdart_delete(path, album_title)
                all_artist_count, local_album_count, local_artist_count, local_cdart_count = xxx_database.new_local_count()
                self.refresh_counts(local_album_count, local_artist_count, local_cdart_count)
                popup_label = utils.lang(32075)
            # elif controlId == 142:  # Backup to backup folder
            else:
                self.single_backup_copy(artist, album_title, path)
                popup_label = utils.lang(32074)
            # else:  # Copy to Unique folder
            #     self.single_unique_copy(artist, album_title, path)
            #     popup_label = utils_ng.lang(32076)
            self.popup(popup_label, self.getControl(140).getSelectedItem().getLabel(), "", "")
            self.setFocusId(140)
            self.populate_local_cdarts(self.getControl(140).getSelectedItem())

        if controlId == 100:  # cdARTS
            self.artwork_type = "cdart"
            self.setFocusId(105)

        if controlId == 101:  # Cover Arts
            self.artwork_type = "cover"
            self.setFocusId(150)

        if controlId == 154:  # Cover Arts
            self.artwork_type = "musicbanner"
            self.setFocusId(200)

        if controlId == 103:  # Advanced
            self.setFocusId(130)

        if controlId == 104:  # Settings
            self.menu_mode = 5
            __settings__.open()

        if controlId == 111:  # Exit
            self.menu_mode = 0
            if __settings__.getSettingBool("enable_missing"):
                self.missing_list()
            self.close()

        if controlId in (180, 181):  # fanart Search Album Artists
            self.menu_mode = 6

        if controlId in (184, 185):  # Clear Logo Search Artists
            self.menu_mode = 7

        if controlId in (197, 198):  # Artist Thumb Search Artists
            self.menu_mode = 9

        if controlId in (205, 207):  # Artist Music Banner Select Artists
            self.menu_mode = 13

        if controlId == 102:
            self.artwork_type = "fanart"
            self.setFocusId(170)
        if controlId == 170:
            self.setFocusId(180)
        if controlId == 171:
            self.setFocusId(182)
        if controlId == 168:
            self.setFocusId(184)
        if controlId == 169:
            self.setFocusId(186)
        if controlId == 193:
            self.setFocusId(197)
        if controlId == 194:
            self.setFocusId(195)
        if controlId == 200:
            self.setFocusId(205)
        if controlId == 201:
            self.setFocusId(207)
        if controlId == 152:
            self.artwork_type = "clearlogo"
            xbmcgui.Window(10001).setProperty("artwork", "clearlogo")
            self.menu_mode = 7
            self.setFocusId(168)
        if controlId == 153:
            self.artwork_type = "artistthumb"
            xbmcgui.Window(10001).setProperty("artwork", "artistthumb")
            self.menu_mode = 9
            self.setFocusId(193)

        if controlId in (180, 181, 184, 185, 197, 198, 205, 206):
            if controlId in (180, 184, 197, 205):
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                self.getControl(120).reset()
                self.local_artists = self.album_artists
                self.populate_artist_list(self.local_artists)
            elif controlId in (181, 185, 198, 206) and __settings__.getExpEnableAllArtits():
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                self.getControl(120).reset()
                self.local_artists = self.all_artists_list
                self.populate_artist_list(self.local_artists)

        if controlId == 167:  # clearLOGO
            artist = {}
            if self.menu_mode == 7:
                url = (self.getControl(167).getSelectedItem().getLabel2()).split("&&&&")[1]
                artist["artist"] = (self.getControl(167).getSelectedItem().getLabel2()).split("&&&&")[0]
                artist["path"] = os.path.join(__settings__.getExpMusicPath(), utils.sanitize_fs(utils.smart_unicode(artist["artist"])))
                selected_item = self.getControl(167).getSelectedPosition()
                if url:
                    message, success, is_canceled = xxx_download.download_art(url, artist, self.artist_menu["local_id"], "clearlogo",
                                                                 "manual", 0)
                    xxx_utils.dialog_msg("close")
                    xxx_utils.dialog_msg("ok", heading=message[0], line1=message[1], line2=message[2], line3=message[3])
                else:
                    settings.log("Nothing to download", xbmc.LOGDEBUG)
                xbmcgui.Window(10001).setProperty("artwork", "clearlogo")
                self.populate_clearlogos(self.artist_menu, selected_item)

        if controlId == 202:  # Music Banner
            artist = {}
            if self.menu_mode == 13:
                url = (self.getControl(202).getSelectedItem().getLabel2()).split("&&&&")[1]
                artist["artist"] = (self.getControl(202).getSelectedItem().getLabel2()).split("&&&&")[0]
                artist["path"] = os.path.join(__settings__.getExpMusicPath(), utils.sanitize_fs(utils.smart_unicode(artist["artist"])))
                selected_item = self.getControl(202).getSelectedPosition()
                if url:
                    message, success, is_canceled = xxx_download.download_art(url, artist, self.artist_menu["local_id"],
                                                                 "musicbanner", "manual", 0)
                    xxx_utils.dialog_msg("close")
                    xxx_utils.dialog_msg("ok", heading=message[0], line1=message[1], line2=message[2], line3=message[3])
                else:
                    settings.log("Nothing to download", xbmc.LOGDEBUG)
                xbmcgui.Window(10001).setProperty("artwork", "musicbanner")
                self.populate_musicbanners(self.artist_menu, selected_item)

        if controlId == 160:  # Fanart Download
            artist = {}
            if self.menu_mode == 6:
                url = (self.getControl(160).getSelectedItem().getLabel2()).split("&&&&")[1]
                artist["artist"] = (self.getControl(160).getSelectedItem().getLabel2()).split("&&&&")[0]
                artist["path"] = os.path.join(__settings__.getExpMusicPath(), utils.sanitize_fs(utils.smart_unicode(artist["artist"])))
                selected_item = self.getControl(160).getSelectedPosition()
                if url:
                    message, success, is_canceled = xxx_download.download_art(url, artist, self.artist_menu["local_id"], "fanart",
                                                                 "manual", 0)
                    xxx_utils.dialog_msg("close")
                    xxx_utils.dialog_msg("ok", heading=message[0], line1=message[1], line2=message[2], line3=message[3])
                else:
                    settings.log("Nothing to download", xbmc.LOGDEBUG)
                xbmcgui.Window(10001).setProperty("artwork", "fanart")
                self.populate_fanarts(self.artist_menu, selected_item)

        if controlId == 199:  # Artist Thumb
            artist = {}
            if self.menu_mode == 9:
                url = (self.getControl(199).getSelectedItem().getLabel2()).split("&&&&")[1]
                artist["artist"] = (self.getControl(199).getSelectedItem().getLabel2()).split("&&&&")[0]
                artist["path"] = os.path.join(__settings__.getExpMusicPath(), utils.sanitize_fs(utils.smart_unicode(artist["artist"])))
                selected_item = self.getControl(199).getSelectedPosition()
                if url:
                    message, success, is_canceled = xxx_download.download_art(url, artist, self.artist_menu["local_id"],
                                                                 "artistthumb", "manual", 0)
                    xxx_utils.dialog_msg("close")
                    xxx_utils.dialog_msg("ok", heading=message[0], line1=message[1], line2=message[2], line3=message[3])
                else:
                    settings.log("Nothing to download", xbmc.LOGDEBUG)
                xbmcgui.Window(10001).setProperty("artwork", "artistthumb")
                self.populate_artistthumbs(self.artist_menu, selected_item)

        if controlId in (182, 186, 187, 183, 106, 151, 195, 196, 207, 208):  # Automatic Download
            self.artwork_type = ""
            if controlId in (106, 151, 186, 182, 195, 207):
                self.local_artists = self.album_artists
                if controlId == 106:  # cdARTs
                    self.menu_mode = 2
                    self.artwork_type = "cdart"
                elif controlId == 151:  # cover arts
                    self.menu_mode = 4
                    self.artwork_type = "cover"
                elif controlId == 186:  # ClearLOGOs
                    self.artwork_type = "clearlogo"
                elif controlId == 182:  # Fanarts
                    self.artwork_type = "fanart"
                elif controlId == 195:  # Artist Thumbs
                    self.artwork_type = "artistthumb"
                elif controlId == 207:  # Artist banner
                    self.artwork_type = "musicbanner"
                download_count, successfully_downloaded = xxx_download.auto_download(self.artwork_type, self.local_artists)
                all_artist_count, local_album_count, local_artist_count, local_cdart_count = xxx_database.new_local_count()
                self.refresh_counts(local_album_count, local_artist_count, local_cdart_count)
                if successfully_downloaded:
                    self.populate_downloaded(successfully_downloaded, self.artwork_type)
            if controlId in (183, 187, 196, 208) and __settings__.getExpEnableAllArtits():
                self.local_artists = self.all_artists_list
                if controlId == 187:  # ClearLOGOs All Artists
                    self.artwork_type = "clearlogo_allartists"
                elif controlId == 183:  # Fanarts All Artists
                    self.artwork_type = "fanart_allartists"
                elif controlId == 196:  # Artist Thumbs All Artists
                    self.artwork_type = "artistthumb_allartists"
                elif controlId == 208:  # Artist Banners All Artists
                    self.artwork_type = "musicbanner_allartists"
                download_count, successfully_downloaded = xxx_download.auto_download(self.artwork_type, self.local_artists)
                all_artist_count, local_album_count, local_artist_count, local_cdart_count = xxx_database.new_local_count()
                self.refresh_counts(local_album_count, local_artist_count, local_cdart_count)
                if successfully_downloaded:
                    self.populate_downloaded(successfully_downloaded, self.artwork_type)

        if controlId == 113:
            self.setFocusId(107)

        if controlId == 114:  # Refresh Artist MBIDs
            self.setFocusId(138)  # change to 138 when selected artist is added to script

        if controlId == 189:  # Edit By Album
            self.setFocusId(123)

        if controlId == 115:  # Find Missing Artist MBIDs
            if __settings__.getExpEnableAllArtits():
                updated_artists, canceled = xxx_database.update_missing_artist_mbid(empty, False, mode="all_artists")
            else:
                updated_artists, canceled = xxx_database.update_missing_artist_mbid(empty, False, mode="album_artists")
            conn = xxx_database.sqlite3.connect(__settings__.getDatabaseFile())
            c = conn.cursor()
            for updated_artist in updated_artists:
                if updated_artist["musicbrainz_artistid"]:
                    try:
                        c.execute('''UPDATE lalist SET musicbrainz_artistid="%s" WHERE local_id=%s''' % (
                            updated_artist["musicbrainz_artistid"], updated_artist["local_id"]))
                    except:
                        settings.log("Error updating database", xbmc.LOGERROR)
                        traceback.print_exc()
                    try:
                        c.execute('''UPDATE alblist SET musicbrainz_artistid="%s" WHERE artist="%s"''' % (
                            updated_artist["musicbrainz_artistid"], updated_artist["name"]))
                    except:
                        settings.log("Error updating database", xbmc.LOGERROR)
                        traceback.print_exc()
                    try:
                        c.execute('''UPDATE local_artists SET musicbrainz_artistid="%s" WHERE local_id=%s''' % (
                            updated_artist["musicbrainz_artistid"], updated_artist["local_id"]))
                    except:
                        settings.log("Error updating database", xbmc.LOGERROR)
                        traceback.print_exc()
            conn.commit()
            c.close()

        if controlId == 139:  # Automatic Refresh Artist MBIDs
            xxx_database.check_artist_mbid(empty, False, mode="album_artists")

        if controlId == 123:
            self.setFocusId(126)

        if controlId == 124:  # Refresh Album MBIDs
            self.setFocusId(147)  # change to 147 when selected album is added to script

        if controlId == 125:
            updated_albums, canceled = xxx_database.update_missing_album_mbid(empty, False)
            conn = xxx_database.sqlite3.connect(__settings__.getDatabaseFile())
            c = conn.cursor()
            for updated_album in updated_albums:
                if updated_album["musicbrainz_albumid"]:
                    try:
                        c.execute(
                            '''UPDATE alblist SET musicbrainz_albumid="%s", musicbrainz_artistid="%s" WHERE album_id=%s''' % (
                                updated_album["musicbrainz_albumid"], updated_album["musicbrainz_artistid"],
                                updated_album["local_id"]))
                    except:
                        settings.log("Error updating database", xbmc.LOGERROR)
                        traceback.print_exc()
            conn.commit()
            c.close()

        if controlId == 126:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            self.getControl(120).reset()
            self.menu_mode = 11
            self.local_artists = xxx_database.get_local_artists_db("album_artists")
            self.populate_artist_list(self.local_artists)

        if controlId == 127:  # Change Album MBID
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            self.getControl(145).reset()
            self.local_albums = xxx_database.get_local_albums_db("all artists")
            self.menu_mode = 12
            self.populate_album_list_mbid(self.local_albums)

        if controlId == 148:  # Automatic Refresh Album MBIDs
            xxx_database.check_album_mbid(empty, False)

        if controlId == 113:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            self.getControl(145).reset()
            self.menu_mode = 10
            if __settings__.getExpEnableAllArtits():
                self.local_artists = xxx_database.get_local_artists_db("all_artists")
            else:
                self.local_artists = xxx_database.get_local_artists_db("album_artists")
            self.populate_artist_list_mbid(self.local_artists)

        if controlId == 158:
            self.getControl(161).reset()
            artist = ""
            album = ""
            albums = []
            artists = []
            canceled = False
            if self.menu_mode == 10:
                kb.setHeading(utils.lang(32164))
                try:
                    kb.setDefault(self.artist_menu["name"])
                except:
                    kb.setDefault(repr(self.artist_menu["name"]))
                kb.doModal()
                while 1:
                    if not (kb.isConfirmed()):
                        canceled = True
                        break
                    else:
                        artist = kb.getText()
                        canceled = False
                        break
                if not canceled:
                    self.artists = xxx_musicbrainz.get_musicbrainz_artists(artist, __settings__.getSettingInt("mbid_match_number"))
                    if self.artists:
                        self.populate_search_list_mbid(self.artists, "artists")
            if self.menu_mode in (11, 12):
                kb.setHeading(utils.lang(32165))
                try:
                    kb.setDefault(self.album_menu["title"])
                except:
                    kb.setDefault(repr(self.album_menu["title"]))
                kb.doModal()
                while 1:
                    if not (kb.isConfirmed()):
                        canceled = True
                        break
                    else:
                        album = kb.getText()
                        canceled = False
                        break
                if not canceled:
                    kb.setHeading(utils.lang(32164))
                    try:
                        kb.setDefault(self.album_menu["artist"])
                    except:
                        kb.setDefault(repr(self.album_menu["artist"]))
                    kb.doModal()
                    while 1:
                        if not (kb.isConfirmed()):
                            canceled = True
                            break
                        else:
                            artist = kb.getText()
                            canceled = False
                            break
                    if not canceled:
                        album, self.albums = xxx_musicbrainz.get_musicbrainz_album(album, artist, 0, __settings__.getSettingInt("mbid_match_number"))
                if self.albums:
                    self.populate_search_list_mbid(self.albums, "albums")

        if controlId == 159:
            self.getControl(161).reset()
            if self.menu_mode == 10:
                self.artists = xxx_musicbrainz.get_musicbrainz_artists(self.artist_menu["name"], __settings__.getSettingInt("mbid_match_number"))
                if self.artists:
                    self.populate_search_list_mbid(self.artists, "artists")
            if self.menu_mode in (11, 12):
                album, self.albums = xxx_musicbrainz.get_musicbrainz_album(self.album_menu["title"], self.album_menu["artist"], 0, __settings__.getSettingInt("mbid_match_number"))
                if self.albums:
                    self.populate_search_list_mbid(self.albums, "albums")

        if controlId == 161:
            if self.menu_mode == 10:
                artist_details = {"musicbrainz_artistid": self.artists[self.getControl(161).getSelectedPosition()]["id"],
                                  "name": self.artists[self.getControl(161).getSelectedPosition()]["name"], "local_id": self.artist_menu["local_id"]}
                xxx_database.user_updates(artist_details, type_="artist")
                self.getControl(145).reset()
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                if __settings__.getExpEnableAllArtits():
                    self.local_artists = xxx_database.get_local_artists_db("all_artists")
                else:
                    self.local_artists = xxx_database.get_local_artists_db("album_artists")
                self.populate_artist_list_mbid(self.local_artists, self.selected_item)
            if self.menu_mode in (11, 12):
                album_details = {"artist": self.albums[self.getControl(161).getSelectedPosition()]["artist"],
                                 "title": self.albums[self.getControl(161).getSelectedPosition()]["title"],
                                 "musicbrainz_artistid": self.albums[self.getControl(161).getSelectedPosition()][
                                     "artist_id"], "musicbrainz_albumid": self.albums[self.getControl(161).getSelectedPosition()]["id"], "path": self.album_menu["path"],
                                 "local_id": self.album_menu["local_id"]}
                xxx_database.user_updates(album_details, type_="album")
                self.getControl(145).reset()
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                if self.menu_mode == 12:
                    self.local_albums = xxx_database.get_local_albums_db("all artists")
                    self.populate_album_list_mbid(self.local_albums, self.selected_item)
                else:
                    self.local_albums = xxx_database.get_local_albums_db(self.artist_menu["name"])
                    self.populate_album_list_mbid(self.local_albums, self.selected_item)

        if controlId == 141:
            local_artists = xxx_database.get_local_artists_db(mode="album_artists")
            if __settings__.getExpEnableAllArtits():
                all_artists = xxx_database.get_local_artists_db(mode="all_artists")
            else:
                all_artists = []
            xxx_fanarttv.first_check(all_artists, local_artists, background=False, update_db=True)
            self.all_artists_list, self.album_artists = xxx_fanarttv.get_recognized(all_artists, local_artists)
            all_artist_count, local_album_count, local_artist_count, local_cdart_count = xxx_database.new_local_count()
            self.refresh_counts(local_album_count, local_artist_count, local_cdart_count)

    def onFocus(self, controlId):
        if controlId not in (122, 140, 160, 167, 199):
            xbmcgui.Window(10001).clearProperty("artwork")
        if controlId == 140:
            self.cdart_icon()
        if controlId in (100, 101, 152, 103, 104, 111):
            xbmcgui.Window(10001).clearProperty("artwork")
            self.menu_mode = 0

    def onAction(self, action):
        if self.menu_mode == 8:
            self.cdart_icon()
        if action.getId() == 10 or action.getButtonCode() in (KEY_BUTTON_BACK, KEY_KEYBOARD_ESC):
            self.close()
            settings.log("Closing", xbmc.LOGNOTICE)
            if __settings__.getSettingBool("enable_missing"):
                self.missing_list()
