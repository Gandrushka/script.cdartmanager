# -*- coding: utf-8 -*-
import datetime
import os
import re

import xbmc
import xbmcaddon
import xbmcvfs

import constants


class Settings:

    # this is shared between all instances
    __addon = None

    def __init__(self):
        if self.__addon is None:
            self.reload()

    # functions
    @classmethod
    def reload(cls, check=False):
        if check:
            log("Looking for settings file %s" % constants.ADDON_FILENAME_SETTINGS, xbmc.LOGNOTICE)
            if not xbmcvfs.exists(cls.getSettingsFile()):  # open settings if settings.xml does not exists
                log("%s File not found, creating path and opening settings" % constants.ADDON_FILENAME_SETTINGS, xbmc.LOGNOTICE)
                cls.open()
            if not xbmcvfs.exists(cls.getSettingsFile()):  # settings could not be created
                raise SystemExit("%s File still not found, exiting " % constants.ADDON_FILENAME_SETTINGS)
        cls.__addon = xbmcaddon.Addon(id=constants.ADDON_ID)

    @classmethod
    def getSettingsFile(cls):
        return xbmc.translatePath(os.path.join(xbmcaddon.Addon(id=constants.ADDON_ID).getAddonInfo('profile'), constants.ADDON_FILENAME_SETTINGS))

    @classmethod
    def open(cls):
        xbmcaddon.Addon(id=constants.ADDON_ID).openSettings()
        cls.reload()

    @classmethod
    def getId(cls):
        return constants.ADDON_ID

    # Addon information
    @classmethod
    def getAddon(cls):
        return cls.__addon

    def getName(self):
        return self.getAddon().getAddonInfo('name')

    def getVersion(self):
        return self.getAddon().getAddonInfo('version')

    def getIcon(self):
        return self.getAddon().getAddonInfo('icon')

    def getFanart(self):
        return self.getAddon().getAddonInfo('fanart')

    def getAuthor(self):
        return self.getAddon().getAddonInfo('author')

    def getPath(self):
        return self.getAddon().getAddonInfo('path')

    def getProfile(self):
        return self.getAddon().getAddonInfo('profile')

    # dynamically created "constant" settings
    def getUserAgent(self):
        return "%s\\%s (https://github.com/stefansielaff/script.cdartmanager)" % (self.getName(), self.getVersion())

    # Configurable settings
    def getSetting(self, setting):
        return self.getAddon().getSetting(setting)

    def getSettingString(self, setting):
        return self.getAddon().getSetting(setting).decode("utf-8")

    def getSettingBool(self, setting):
        return self.getSetting(setting) == "true"

    def getSettingInt(self, setting):
        try:
            return int(self.getSetting(setting))
        except ValueError:
            return -1

    def getSettingPath(self, setting):
        return xbmc.translatePath(self.getSetting(setting)).decode("utf-8")

    # explicitly accessible settings which are often used, @TODO: optimize performance

    def getExpEnableAllArtits(self):
        return self.getSettingBool("enable_all_artists")

    def getExpMusicPath(self):
        return self.getSettingPath("music_path")

    # Addon directory and related functions
    def getResourceBasePath(self):
        return xbmc.translatePath(os.path.join(self.getPath(), constants.ADDON_DIRNAME_RESOURCES))

    def getSkinImage(self, filename):
        return os.path.join(self.getResourceBasePath(), "skins", constants.SKIN_FOLDER, "media", filename)

    # Working directory and related functions
    def getWorkBasePath(self):
        return xbmc.translatePath(self.getProfile())

    def getWorkDir(self, dirname):
        result = os.path.join(self.getWorkBasePath(), dirname, '')
        if not xbmcvfs.exists(result):
            xbmcvfs.mkdirs(result)
        return result

    def getWorkFile(self, filename, dirname=None):
        if dirname is None:
            return os.path.join(self.getWorkBasePath(), filename)
        else:
            return os.path.join(self.getWorkDir(dirname), filename)

    def getDataStoreBaseDir(self):
        return self.getWorkDir(constants.DS_DIR)

    def getDataStoreFile(self, file_name):
        result = os.path.join(self.getDataStoreBaseDir(), file_name)
        return result

    def getDatabaseFile(self):
        return self.getWorkFile(constants.DB_FILENAME)

    def getDatabaseFileBackupNow(self):
        current_date = datetime.datetime.today().strftime("%m-%d-%Y-%H%M")
        return self.getWorkFile(constants.DB_FILENAME_BACKUP % current_date)

    def getDatabaseFileJournal(self):
        return self.getWorkFile(constants.DB_FILENAME_JOURNAL)

    def getDatabaseFileUpdate(self):
        return self.getWorkFile(constants.DB_FILENAME_UPDATE)

    def isDevMode(self):
        return xbmcvfs.exists(self.getWorkFile("DEVMODE"))

    def to_log(self):
        level = xbmc.LOGNOTICE
        try:
            log("Settings:\n", level)
            base_path = self.getSettingsFile()
            settings_file = xbmcvfs.File(base_path)
            settings_list = []
            for setting_line in settings_file.read().splitlines():
                match = re.search('<setting id="(.*?)"', setting_line)
                if match:
                    settings_list.append(match.group(1))
            settings_file.close()
            for setting in settings_list:
                    log("%25s: %s" % (setting, self.getSetting(setting)), level)
        except:
            log("Settings to log failed")


# defined here to avoid circulars
def log(text, severity=constants.LOG_DEFAULTLEVEL):
    if type(text).__name__ == 'unicode':
        text = text.encode('utf-8')
    message = ('[%s] - %s' % (constants.ADDON_ID, text.__str__()))
    xbmc.log(msg=message, level=severity)
