# -*- coding: utf-8 -*-
import errno
import htmlentitydefs
import os
import re
import traceback
import urllib

import xbmc
import xbmcgui
import xbmcvfs

import constants
import settings
import utils
import xxx_file_item

__settings__ = settings.Settings()

dialog = xbmcgui.DialogProgress()


def get_unicode(to_decode):
    final = []
    try:
        to_decode.encode('utf8')
        return to_decode
    except:
        while True:
            try:
                final.append(to_decode.decode('utf8'))
                break
            except UnicodeDecodeError, exc:
                # everything up to crazy character should be good
                final.append(to_decode[:exc.start].decode('utf8'))
                # crazy character is probably latin1
                final.append(to_decode[exc.start].decode('latin1'))
                # remove already encoded stuff
                to_decode = to_decode[exc.start + 1:]
        return "".join(final)


def clear_image_cache(url):
    thumb = xxx_file_item.Thumbnails().get_cached_picture_thumb(url)
    png = os.path.splitext(thumb)[0] + ".png"
    dds = os.path.splitext(thumb)[0] + ".dds"
    jpg = os.path.splitext(thumb)[0] + ".jpg"
    if xbmcvfs.exists(thumb):
        xbmcvfs.delete(thumb)
    if xbmcvfs.exists(png):
        xbmcvfs.delete(png)
    if xbmcvfs.exists(jpg):
        xbmcvfs.delete(jpg)
    if xbmcvfs.exists(dds):
        xbmcvfs.delete(dds)


def get_html_source(url, filename, save_file=True, overwrite=False):
    settings.log("Retrieving HTML Source", xbmc.LOGDEBUG)
    settings.log("Fetching URL: %s" % url, xbmc.LOGDEBUG)
    error = False
    htmlsource = "null"

    file_name = None
    if save_file:
        filename += ".json"
        file_name = __settings__.getWorkFile(filename, constants.WORKDIR_TEMP_XML)

    class AppURLopener(urllib.FancyURLopener):
        version = __settings__.getUserAgent()

    urllib._urlopener = AppURLopener()
    for i in range(0, 4):
        try:
            if save_file:
                if xbmcvfs.exists(file_name) and not overwrite:
                    settings.log("Retrieving local source", xbmc.LOGDEBUG)
                    sock = open(file_name, "r")
                else:
                    settings.log("Retrieving online source", xbmc.LOGDEBUG)
                    urllib.urlcleanup()
                    sock = urllib.urlopen(url)
            else:
                urllib.urlcleanup()
                sock = urllib.urlopen(url)
            htmlsource = sock.read()
            if save_file and htmlsource not in ("null", ""):
                if not xbmcvfs.exists(file_name) or overwrite:
                    file(file_name, "w").write(htmlsource)
            sock.close()
            break
        except IOError, e:
            settings.log("error: %s" % e, xbmc.LOGERROR)
            settings.log("e.errno: %s" % e.errno, xbmc.LOGERROR)
            if not e.errno == "socket error":
                settings.log("errno.errorcode: %s" % errno.errorcode[e.errno], xbmc.LOGERROR)
        except:
            traceback.print_exc()
            settings.log("!!Unable to open page %s" % url, xbmc.LOGDEBUG)
            error = True
    if error:
        return "null"
    else:
        settings.log("HTML Source:\n%s" % htmlsource, xbmc.LOGDEBUG)
        if htmlsource == "":
            htmlsource = "null"
        return htmlsource


def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is

    return re.sub("&#?\w+;", fixup, text)


# centralized Dialog function from Artwork Downloader
# Define dialogs
def dialog_msg(action,
               percent=0,
               heading='',
               line1='',
               line2='',
               line3='',
               background=False,
               nolabel=utils.lang(32179),
               yeslabel=utils.lang(32178)):
    # Fix possible unicode errors 
    heading = heading.encode('utf-8', 'ignore')
    line1 = line1.encode('utf-8', 'ignore')
    line2 = line2.encode('utf-8', 'ignore')
    line3 = line3.encode('utf-8', 'ignore')
    # Dialog logic
    if not heading == '':
        heading = __settings__.getName() + " - " + heading
    else:
        heading = __settings__.getName()
    if not line1:
        line1 = ""
    if not line2:
        line2 = ""
    if not line3:
        line3 = ""
    if not background:
        if action == 'create':
            dialog.create(heading, line1, line2, line3)
        if action == 'update':
            dialog.update(percent, line1, line2, line3)
        if action == 'close':
            dialog.close()
        if action == 'iscanceled':
            return dialog.iscanceled()
            #if dialog.iscanceled():
            #    return True
            #else:
            #    return False
        if action == 'okdialog':
            xbmcgui.Dialog().ok(heading, line1, line2, line3)
        if action == 'yesno':
            return xbmcgui.Dialog().yesno(heading, line1, line2, line3, nolabel, yeslabel)
    if background:
        if action == 'create' or action == 'okdialog':
            if line2 == '':
                msg = line1
            else:
                msg = line1 + ': ' + line2
            xbmc.executebuiltin("XBMC.Notification(%s, %s, 7500, %s)" % (heading, msg, __settings__.getIcon()))


