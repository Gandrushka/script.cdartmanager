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

CONTROLID_MAIN_MENU = 9011
CONTROLID_TOP_LABEL = 9021
CONTROLID_TOP_LOADING = 9022

CONTROLID_ACTION_BASE = 9100


class GUI(xbmcgui.WindowXMLDialog):

    __main_menu = None
    __main_selected = None
    __dash_active = None

    __datastore = None

    def __init__(self, xmlFilename, scriptPath, *args, **kwargs):
        self.DASHBOARD = xbmcgui.ListItem(utils.lang(32500), "DASHBOARD", iconImage="icons/ic_cloud_download_white_48dp_2x.png")
        self.ALBUMS = xbmcgui.ListItem(utils.lang(132, False), "ALBUMS", iconImage="icons/ic_album_white_48dp_2x.png")
        self.ARTISTS = xbmcgui.ListItem(utils.lang(133, False), "ARTISTS", iconImage="icons/ic_people_outline_white_48dp_2x.png")
        self.SETTINGS = xbmcgui.ListItem(utils.lang(5, False), "SETTINGS", iconImage="icons/ic_settings_white_48dp_2x.png")
        self.EXIT = xbmcgui.ListItem(utils.lang(13012, False), "EXIT", iconImage="icons/ic_power_settings_new_white_48dp_2x.png")
        super(GUI, self).__init__(xmlFilename, scriptPath, *args, **kwargs)

    def onInit(self):
        # Main Menu
        self.__main_menu = self.getControl(CONTROLID_MAIN_MENU)
        self.__main_menu.addItems([self.DASHBOARD, self.ALBUMS, self.ARTISTS, self.SETTINGS, self.EXIT])
        self.setMainSelected(self.__main_menu.getSelectedItem())
        self.setFocus(self.__main_menu)

    def onClick(self, control_id):
        settings.log("Click: %s" % control_id)
        if control_id == CONTROLID_MAIN_MENU and self.__main_selected is not None:
            main_action = self.__main_selected.getLabel2()
            if main_action == "EXIT":
                self.exit()

        if control_id == 9101:
            self.getControl(CONTROLID_TOP_LOADING).setVisible(True)
            self.getControl(9311).setVisible(False)
            self.getControl(9321).setVisible(False)
            self.__datastore.update_datastore("albums", self.dashboardCallback)
            self.__datastore.update_datastore("artists", self.dashboardCallback)
            self.updateMainSelection(True)
            self.getControl(CONTROLID_TOP_LOADING).setVisible(False)

    def onControl(self, control_id):
        pass

    def onAction(self, action):

        # settings.log("Action: %s" % action)

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
        try:
            if self.__main_selected is None or force or self.__main_selected.getLabel2() != control.getLabel2():
                self.__main_selected = control
                try:
                    self.__dash_active = self.getControl(CONTROLID_ACTION_BASE + (self.__main_menu.getSelectedPosition()*100))
                    self.__main_menu.controlRight(self.__dash_active)
                except:
                    self.__dash_active = None
                    self.__main_menu.con.controlRight(None)
                self.updateMainSelection()
        except:
            pass

    def updateMainSelection(self, force=False):

        self.getControl(CONTROLID_TOP_LABEL).setLabel(self.__main_selected.getLabel())
        self.getControl(CONTROLID_TOP_LOADING).setVisible(True)

        selected = self.__main_selected.getLabel2()
        if selected == self.DASHBOARD.getLabel2():
            if self.__datastore is None or force:
                self.__datastore = datastore.Datastore(self.dashboardCallback)
                percent = (100 * (self.__datastore.albums_count() - self.__datastore.albums_count_no_mbid()) / self.__datastore.albums_count())
                settings.log("P: %s %s" % (self.__datastore.albums_count(), self.__datastore.albums_count_no_mbid()))
                self.getControl(9311).setLabel("%s%%" % percent)
                self.getControl(9311).setVisible(True)
                percent = (100 * (self.__datastore.artists_count() - self.__datastore.artists_count_no_mbid()) / self.__datastore.artists_count())
                self.getControl(9321).setLabel("%s%%" % percent)
                self.getControl(9321).setVisible(True)

        self.getControl(CONTROLID_TOP_LOADING).setVisible(False)

    def dashboardCallback(self, index, size, artist, album_title=None):
        if album_title is None:
            control = self.getControl(9320)
        else:
            control = self.getControl(9310)

        if index == (size-1):
            control.setLabel("%s" % size)
        else:
            control.setLabel("%s / %s" % (index, size))
        return False  # Cancelled

    def exit(self):
        self.close()
        settings.log("Closing", xbmc.LOGNOTICE)

    @staticmethod
    def bold(txt):
        return "[B]%s[/B]" % txt
