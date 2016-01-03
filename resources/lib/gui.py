# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import settings
import utils

__settings__ = settings.Settings()

kb = xbmc.Keyboard()

KEY_BUTTON_BACK = 275
KEY_KEYBOARD_ESC = 61467

CONTROLID_MAIN_MENU = 9100


class GUI(xbmcgui.WindowXMLDialog):

    __main_menu = None
    __main_selected = None

    def onInit(self):

        # Main Menu
        self.__main_menu = self.getControl(9100)
        main_items = [
            xbmcgui.ListItem(utils.lang(32500), "DASHBOARD", iconImage="icons/ic_cloud_download_white_48dp_2x.png"),
            xbmcgui.ListItem(utils.lang(32501), "ALBUMS", iconImage="icons/ic_album_white_48dp_2x.png"),
            xbmcgui.ListItem(utils.lang(32502), "ARTISTS", iconImage="icons/ic_people_outline_white_48dp_2x.png"),
            xbmcgui.ListItem(utils.lang(32503), "SETTINGS", iconImage="icons/ic_settings_white_48dp_2x.png"),
            xbmcgui.ListItem(utils.lang(32504), "EXIT", iconImage="icons/ic_power_settings_new_white_48dp_2x.png"),
        ]
        self.__main_menu.addItems(main_items)
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
            self.__main_selected = self.__main_menu.getSelectedItem()

        if self.__main_selected is not None:
            pass

        if action.getButtonCode() in (KEY_BUTTON_BACK, KEY_KEYBOARD_ESC):
            self.exit()

    def exit(self):
        self.close()
        settings.log("Closing", xbmc.LOGNOTICE)
