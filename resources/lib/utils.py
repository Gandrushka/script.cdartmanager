import xbmc
import xbmcgui
import settings

__settings__ = settings.Settings()


def lang(id_):
    return __settings__.getAddon().getLocalizedString(id_)


def yesno_dialog(heading, line1='', line2='', line3='',):
    return xbmcgui.Dialog().yesno(heading, line1, line2, line3, lang(32179), lang(32178))


class ProgressDialog:

    __dialog = None

    def __init__(self):
        pass

    def artist_album(self, position, size, artist, album=None):
        if size > 0:
            percent = int((position / float(size)) * 100)
            if not self.__dialog:
                self.__dialog = xbmcgui.DialogProgress()
                self.__dialog.create(heading=lang(32134), line1="", line2="", line3="")
            if album is None:
                self.__dialog.update(percent=percent, line1="%s:" % lang(32137), line2=smart_unicode(artist), line3="")
            else:
                self.__dialog.update(percent=percent, line1="%s:" % lang(32138), line2="%s - %s" % (smart_unicode(artist), smart_unicode(album)))
            # xbmc.sleep(500)
            return self.__dialog.iscanceled()

    def close(self):
        if self.__dialog:
            self.__dialog.close()


def is_true(value):
    return value in ("true", "True")


def is_mbid(mbid):
    # a very basic check to validate a MBID
    return mbid is not None and len(mbid) == 36 and len(mbid.replace("-", "")) == 32


def sanitize_fs(text, force=False):

    if force or __settings__.getSettingBool("enable_replace_illegal"):
        original = list(text)
        illegal_characters = list(__settings__.getSetting("illegal_characters"))
        replace_character = __settings__.getSetting("replace_character")
        change_period_atend = __settings__.getSettingBool("change_period_atend")
        final = []
        for i in original:
            if i in illegal_characters:
                final.append(replace_character)
            else:
                final.append(i)
        temp = "".join(final)
        if temp.endswith(".") and change_period_atend:
            text = temp[:len(temp) - 1] + replace_character
        else:
            text = temp
        return smart_unicode(text.strip())
    else:
        return text


def smart_unicode(s):
    if not s:
        return ''
    try:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'UTF-8')
        elif not isinstance(s, unicode):
            s = unicode(s, 'UTF-8')
    except:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'ISO-8859-1')
        elif not isinstance(s, unicode):
            s = unicode(s, 'ISO-8859-1')
    return s


def smart_utf8(s):
    return smart_unicode(s).encode('utf-8')