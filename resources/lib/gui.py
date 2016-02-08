# -*- coding: utf-8 -*-
import traceback

import xbmc
import xbmcgui

import datastore
import utils_lang as ul
import settings

# kb = xbmc.Keyboard()

KEY_BUTTON_BACK = 275
KEY_KEYBOARD_ESC = 61467

CID_MAIN_MENU = 9011
CID_TOP_LABEL = 9021
CID_TOP_LOADING = 9022

CID_ACTION_BASE = 9100

CID_DASH_START = 9101
CID_DASH_ALBUM_COUNT = 9110
CID_DASH_ALBUM_PERCENT = 9111
CID_DASH_ARTIST_COUNT = 9120
CID_DASH_ARTIST_PERCENT = 9121

CID_ALBUMS_LIST = 9210


class GUI(xbmcgui.WindowXMLDialog):

    def __init__(self, xmlFilename, scriptPath, *args, **kwargs):

        self.__settings__ = settings.Settings()

        self.__main_menu = None
        self.__main_selected = None
        self.__dash_active = None
        self.__datastore = None

        self.DASHBOARD = xbmcgui.ListItem(ul.LNG_DASHBOARD, "DASHBOARD", iconImage="icons/ic_cloud_download_white_48dp_2x.png")
        self.ALBUMS = xbmcgui.ListItem(ul.LNG_ALBUMS, "ALBUMS", iconImage="icons/ic_album_white_48dp_2x.png")
        self.ARTISTS = xbmcgui.ListItem(ul.LNG_ARTISTS, "ARTISTS", iconImage="icons/ic_people_outline_white_48dp_2x.png")
        self.SETTINGS = xbmcgui.ListItem(ul.LNG_SETTINGS, "SETTINGS", iconImage="icons/ic_settings_white_48dp_2x.png")
        self.EXIT = xbmcgui.ListItem(ul.LNG_EXIT, "EXIT", iconImage="icons/ic_power_settings_new_white_48dp_2x.png")
        super(GUI, self).__init__(xmlFilename, scriptPath, *args, **kwargs)

    def onInit(self):
        # Main Menu
        self.__main_menu = self.gc(CID_MAIN_MENU)
        self.__main_menu.addItems([self.DASHBOARD, self.ALBUMS, self.ARTISTS, self.SETTINGS, self.EXIT])
        self.setMainSelected(self.__main_menu.getSelectedItem())
        self.setFocus(self.__main_menu)

    def onClick(self, control_id):
        settings.log("Click: %s" % control_id)
        if control_id == CID_MAIN_MENU and self.__main_selected is not None:
            main_action = self.__main_selected.getLabel2()
            if main_action == "EXIT":
                self.exit()

        if control_id == CID_DASH_START:
            if self.gcl(control_id) == ul.LNG_START:
                self.sc(CID_TOP_LOADING)
                self.hc(CID_DASH_ALBUM_PERCENT)
                self.hc(CID_DASH_ARTIST_PERCENT)
                self.scl(control_id, ul.LNG_CANCEL)
                self.__datastore.update_datastore("all", self.dashboardCallback)
                self.ec(self.scl(control_id, ul.LNG_START))
                self.updateMainSelection()
                self.hc(CID_TOP_LOADING)
            else:
                self.dc(self.scl(control_id, ul.LNG_WAIT))

    def onControl(self, control_id):
        pass

    def onAction(self, action):

        # settings.log("Action: %s" % action)

        if self.getFocusId() == 0:
            self.sf(CID_MAIN_MENU)

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
                    self.__dash_active = self.gc(CID_ACTION_BASE + (self.__main_menu.getSelectedPosition() * 100))
                    self.__main_menu.controlRight(self.__dash_active)
                except SystemError:
                    settings.log("InnerException in setMainSelected")
                    traceback.print_exc()
                    self.__dash_active = None
                    self.__main_menu.controlRight(None)
                self.updateMainSelection()
        except SystemError:
            settings.log("OuterException in setMainSelected")
            traceback.print_exc()
            pass

    def updateMainSelection(self, force=False):

        self.scl(CID_TOP_LABEL, self.__main_selected.getLabel())
        self.sc(CID_TOP_LOADING)

        selected = self.__main_selected.getLabel2()
        if selected == self.DASHBOARD.getLabel2():
            if self.__datastore is None or force:
                self.__datastore = datastore.Datastore(self.dashboardCallback)
            percent = (100 * self.__datastore.albums_count_mbid / self.__datastore.albums_count)
            self.sc(self.scl(CID_DASH_ALBUM_PERCENT, "%s%%" % percent))
            percent = (100 * self.__datastore.artists_count_mbid / self.__datastore.artists_count)
            self.sc(self.scl(CID_DASH_ARTIST_PERCENT, "%s%%" % percent))

        self.hc(CID_TOP_LOADING)

    def dashboardCallback(self, index, size, result):

        if result is not None:
            if 'cdart_album' in result:
                dash_control = self.gc(CID_DASH_ALBUM_COUNT)

                li = xbmcgui.ListItem(result['label'])
                self.gc(CID_ALBUMS_LIST).addItem(li)

            else:
                dash_control = self.gc(CID_DASH_ALBUM_COUNT)

            if index == (size-1):
                dash_control.setLabel("%s" % size)
            else:
                dash_control.setLabel("%s / %s" % (index, size))

        return self.gcl(CID_DASH_START) == ul.LNG_WAIT  # Cancelled

    def exit(self):
        self.close()
        settings.log("Closing", xbmc.LOGNOTICE)

    @staticmethod
    def bold(txt):
        return "[B]%s[/B]" % txt

    # Shortcuts for standard control methods, all setters must return
    # the affected control to allow command chaining (sorry for not being pythonic ;)

    # shortcut for getControl
    def gc(self, control_or_id):
        if type(control_or_id) == int:
            return self.getControl(control_or_id)
        else:
            settings.log(str(control_or_id))
            return control_or_id

    # get label
    def gcl(self, control):
        c = self.gc(control)
        return c.getLabel()

    # hide control
    def hc(self, control_id):
        c = self.gc(control_id)
        c.setVisible(False)
        return c

    # show control
    def sc(self, control_id):
        c = self.gc(control_id)
        c.setVisible(True)
        return c

    # disable control
    def dc(self, control_id):
        c = self.gc(control_id)
        c.setEnabled(False)
        return c

    # enable control
    def ec(self, control_id):
        c = self.gc(control_id)
        c.setEnabled(True)
        return c

    # set focus
    def sf(self, control_id):
        c = self.gc(control_id)
        self.setFocus(c)
        return c

    # set label
    def scl(self, control_id, label):
        c = self.gc(control_id)
        c.setLabel(label)
        return c

