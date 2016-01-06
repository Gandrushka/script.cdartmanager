# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import settings
import utils
import datastore

__settings__ = settings.Settings()

kb = xbmc.Keyboard()

KEY_BUTTON_BACK = 275
KEY_KEYBOARD_ESC = 61467

CONTROLID_MAIN_MENU = 9100
CONTROLID_TOP_LABEL = 9201
CONTROLID_TOP_LOADING = 9202


class GUI(xbmcgui.WindowXMLDialog):

    __main_menu = None
    __main_selected = None

    __datastore = None

    def __init__(self, xmlFilename, scriptPath, *args, **kwargs):
        self.DASHBOARD = xbmcgui.ListItem(utils.lang(32500), "DASHBOARD", iconImage="icons/ic_cloud_download_white_48dp_2x.png")
        self.ALBUMS = xbmcgui.ListItem(utils.lang(32501), "ALBUMS", iconImage="icons/ic_album_white_48dp_2x.png")
        self.ARTISTS = xbmcgui.ListItem(utils.lang(32502), "ARTISTS", iconImage="icons/ic_people_outline_white_48dp_2x.png")
        self.SETTINGS = xbmcgui.ListItem(utils.lang(32503), "SETTINGS", iconImage="icons/ic_settings_white_48dp_2x.png")
        self.EXIT = xbmcgui.ListItem(utils.lang(32504), "EXIT", iconImage="icons/ic_power_settings_new_white_48dp_2x.png")
        super(GUI, self).__init__(xmlFilename, scriptPath, *args, **kwargs)

    def onInit(self):
        # Main Menu
        self.__main_menu = self.getControl(9100)
        self.__main_menu.addItems([self.DASHBOARD, self.ALBUMS, self.ARTISTS, self.SETTINGS, self.EXIT])
        self.setMainSelected(self.__main_menu.getSelectedItem())
        self.setFocus(self.__main_menu)

    def onClick(self, control_id):
        settings.log("Click: %s" % control_id)
        if control_id == CONTROLID_MAIN_MENU and self.__main_selected is not None:
            main_action = self.__main_selected.getLabel2()
            if main_action == "EXIT":
                self.exit()

    def onControl(self, control_id):
        pass

    def onAction(self, action):

        settings.log("Action: %s" % action)

        if self.getFocusId() == 0:
            self.setFocusId(CONTROLID_MAIN_MENU)

        if self.__main_menu is not None:
            self.setMainSelected(self.__main_menu.getSelectedItem())

        if self.__main_selected is not None:
            pass

        if action.getButtonCode() in (KEY_BUTTON_BACK, KEY_KEYBOARD_ESC):
            self.exit()

    def setMainSelected(self, control, force=False):
        # handles selection in main menu, only if selection is changed
        if self.__main_selected is None or force or self.__main_selected.getLabel2() != control.getLabel2():
            self.__main_selected = control
            self.getControl(CONTROLID_TOP_LABEL).setLabel(self.bold(self.__main_selected.getLabel()))
            self.updateMainSelection()

    def updateMainSelection(self, force=False):
        self.getControl(CONTROLID_TOP_LOADING).setVisible(True)

        selected = self.__main_selected.getLabel2()
        if selected == self.DASHBOARD.getLabel2():
            if self.__datastore is None or force:
                self.__datastore = datastore.Datastore(self.dashboardCallback)
#                percent = self.__datastore.albums_count_no_mbid()/self.__datastore.albums_count()
#                self.getControl(9311).setLabel(str(percent))
#                self.getControl(9321).setLabel(str(self.__datastore.artists_count_no_mbid()/self.__datastore.artists_count()*100))

        self.getControl(CONTROLID_TOP_LOADING).setVisible(False)

    def dashboardCallback(self, index, albums_len, album_artist, album_title=None):
        if album_title is None:
            self.getControl(9320).setLabel(str(index))
        else:
            self.getControl(9310).setLabel(str(index))

    def exit(self):
        self.close()
        settings.log("Closing", xbmc.LOGNOTICE)

    @staticmethod
    def bold(txt):
        return "[B]%s[/B]" % txt
