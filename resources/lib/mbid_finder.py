import time
import requests
import xbmc
import constants
import settings
import utils

__settings__ = settings.Settings()


class ArtistAlbum(object):

    def __init__(self, artist=None, album=None):
        self.__artist = artist
        self.__album = album

    def __str__(self):
        artist = self.artist
        if self.is_va:
            artist = '[VA]'
        return 'artist=%s, album=%s' % (artist, self.album)

    @classmethod
    def from_other(cls, other):
        return cls(other.artist, other.album)

    @property
    def has_any(self):
        return self.has_artist or self.has_album

    @property
    def has_all(self):
        return self.has_artist and self.has_album

    @property
    def artist(self):
        return self.__artist

    @artist.setter
    def artist(self, value):
        self.__artist = utils.smart_unicode(value)

    @property
    def has_artist(self):
        return self.artist is not None and self.artist != ''

    @property
    def is_va(self):
        return self.has_artist and self.artist == constants.MUSICBRAINZ_VA_MBID

    @property
    def album(self):
        return self.__album

    @album.setter
    def album(self, value):
        self.__album = utils.smart_unicode(value)

    @property
    def has_album(self):
        return self.album is not None and self.album != ''

    def album_equals(self, other_album):
        return self.__equals(self.album, utils.smart_unicode(other_album))

    def artist_equals(self, other_artist):
        return self.__equals(self.artist, utils.smart_unicode(other_artist))

    def equals(self, other):
        if other is None:
            return False
        else:
            return self.artist_equals(other.artist) and self.album_equals(other.album)

    @staticmethod
    def __equals(s1, s2):
        if s1 is None:
            return s2 is None
        elif s2 is None:
            return False
        else:
            return s1.upper().lower() == s2.upper().lower()


class MBIDResult(ArtistAlbum):

    def __init__(self, artist=None, album=None):
        super(self.__class__, self).__init__(artist, album)
        self.__confidence = None

    def __str__(self):
        artist = self.artist
        if self.is_va:
            artist = '[VA]'
        return 'artist=%s, album=%s' % (artist, self.album)

    @property
    def has_artist(self):
        return utils.is_mbid(self.artist)

    @property
    def has_album(self):
        return utils.is_mbid(self.album)

    @property
    def confidence(self):
        return self.__confidence

    @confidence.setter
    def confidence(self, value):
        self.__confidence = value


class RealNameResult(ArtistAlbum):
    pass


class MBIDFinder(ArtistAlbum):

    def find(self):
        if self.__class__.__name__ != 'MBIDFinder':
            raise NotImplementedError

        mbid_result = MBIDResult()
        settings.log('MBIDFinder starting, %s' % self, xbmc.LOGNOTICE)

        mb_va = MusicBrainzVA()
        if mb_va.is_va(self.artist):
            mbid_result.artist = constants.MUSICBRAINZ_VA_MBID
            if self.has_album:
                va_album = MusicbrainzMBIDFinder.from_other(self)
                va_album.artist = constants.MUSICBRAINZ_VA_MBID
                mbid_result = va_album.find()
        else:
            if not mbid_result.has_any:
                mbid_result = TadbMBIDFinder.from_other(self).find()
            if not mbid_result.has_any:
                real_name = RealNameFinder.from_other(self).find()
                if not real_name.has_any or real_name.equals(self):
                    real_name = None
                if not mbid_result.has_any and real_name is not None:
                    mbid_result = TadbMBIDFinder.from_other(real_name).find()
                if not mbid_result.has_any:
                    mbid_result = MusicbrainzMBIDFinder.from_other(self).find()
                if not mbid_result.has_any and real_name is not None:
                    mbid_result = MusicbrainzMBIDFinder.from_other(real_name).find()
        return mbid_result


class TadbMBIDFinder(MBIDFinder):

    def find(self):
        settings.log('  TadbMBIDFinder starting, %s' % self, xbmc.LOGNOTICE)
        result = MBIDResult()
        if self.artist is not None:
            if self.album is not None:
                url = constants.TADB_ALBUM_SERVLET
                params = {'s': self.artist, 'a': self.album}
            else:
                url = constants.TADB_ARTIST_SERVLET
                params = {'s': self.artist}
            try:
                r = requests.get(url, params, headers={'user-agent': __settings__.getUserAgent()})
                json = r.json()
                if 'artists' in json and json['artists'] is not None:
                    bestmatch = json['artists'][0]
                    if 'strMusicBrainzID' in bestmatch and utils.is_mbid(bestmatch['strMusicBrainzID']):
                        result.artist = bestmatch['strMusicBrainzID']
                if 'album' in json and json['album'] is not None:
                    bestmatch = json['album'][0]
                    if 'strMusicBrainzID' in bestmatch and utils.is_mbid(bestmatch['strMusicBrainzID']):
                        result.album = bestmatch['strMusicBrainzID']
                    if 'strMusicBrainzArtistID' in bestmatch and utils.is_mbid(bestmatch['strMusicBrainzArtistID']):
                        result.artist = bestmatch['strMusicBrainzArtistID']
                settings.log('  TheAudioDB result: %s' % result, xbmc.LOGNOTICE)
            except:
                settings.log('  TheAudioDB result: failed', xbmc.LOGWARNING)

        if result.has_any:
            result.confidence = "TADB"

        return result


class MusicbrainzMBIDFinder(MBIDFinder):

    def find(self):
        settings.log('  MusicbrainzMBIDFinder starting, %s' % self, xbmc.LOGNOTICE)
        result = MBIDResult()
        if self.album is not None:
            url = constants.MUSICBRAINZ_ALBUM_SERVLET
            params = dict(constants.MUSICBRAINZ_DEFAULT_PARAMS)
            if self.is_va:
                params.update({'query': 'arid:%s AND %s' % (self.artist, self.album)})
            else:
                params.update({'query': 'artist:%s AND "%s"' % (self.artist, self.album)})
            try:
                r = ThrottledMusicbrainzRequest().get(url, params, headers={'user-agent': __settings__.getUserAgent()})
                settings.log('  MusicbrainzMBIDFinder url: %s' % r.url)
                json = r.json()
                settings.log(json)
                if 'releases' in json and json['releases'] is not None and len(json['releases']) > 0:
                    bestmatch = json['releases'][0]
                    if 'id' in bestmatch and utils.is_mbid(bestmatch['id']):
                        result.album = bestmatch['id']
                    if 'artist-credit' in bestmatch and len(bestmatch['artist-credit']) > 0:
                        bestmatch_artist = bestmatch['artist-credit'][0]['artist']
                        settings.log(bestmatch_artist)
                        if 'id' in bestmatch_artist and utils.is_mbid(bestmatch_artist['id']):
                            result.artist = bestmatch_artist['id']
                settings.log('  Musicbrainz result: %s' % result, xbmc.LOGNOTICE)
            except:
                settings.log('  Musicbrainz result: failed', xbmc.LOGWARNING)

        elif self.artist is not None:
            if not result.has_any:
                url = constants.MUSICBRAINZ_ARTIST_SERVLET
                params = dict(constants.MUSICBRAINZ_DEFAULT_PARAMS)
                params.update({'query': '"%s"' % self.artist})
                try:
                    r = ThrottledMusicbrainzRequest().get(url, params, headers={'user-agent': __settings__.getUserAgent()})
                    settings.log('  MusicbrainzMBIDFinder url: %s' % r.url)
                    json = r.json()
                    if 'artists' in json and json['artists'] is not None and len(json['artists']) > 0:
                        bestmatch = json['artists'][0]
                        if 'id' in bestmatch and utils.is_mbid(bestmatch['id']):
                            result.artist = bestmatch['id']
                    settings.log('  Musicbrainz result: %s' % result, xbmc.LOGNOTICE)
                except:
                    settings.log('  Musicbrainz result: failed', xbmc.LOGWARNING)

        return result


class MusicBrainzVA:
    """Get Musicbrainz Various Artists entity"""
    __aliases = []

    def __init__(self):
        if len(MusicBrainzVA.__aliases) == 0:
            settings.log('Initializing MusicBrainz VA collection', xbmc.LOGNOTICE)
            more_va_list = __settings__.getSettingString('va_aliases')
            for va in more_va_list.split(','):
                MusicBrainzVA.__aliases.append(utils.smart_unicode(va).upper().lower())

            url = constants.MUSICBRAINZ_VA_SERVLET
            params = dict(constants.MUSICBRAINZ_VA_PARAMS)
            try:
                r = ThrottledMusicbrainzRequest().get(url, params, headers={'user-agent': __settings__.getUserAgent()})
                settings.log('MusicBrainzVA url: %s' % r.url)
                json = r.json()
                if 'aliases' in json:
                    for entry in json['aliases']:
                        if 'name' in entry:
                            MusicBrainzVA.__aliases.append(entry['name'].upper().lower())

                    settings.log('MusicBrainzVA result: %d aliases' % len(MusicBrainzVA.__aliases), xbmc.LOGNOTICE)
            except:
                settings.log('MusicBrainzVA result: failed', xbmc.LOGWARNING)

            self.__aliases = list(MusicBrainzVA.__aliases)

    def is_va(self, artist_name):
        return artist_name is None or artist_name.upper().lower() in self.__aliases


class ThrottledMusicbrainzRequest:
    """Throttles a Musicbrainz requests to honor API restrictions"""
    __last_request = 0

    def __init__(self):
        pass

    @classmethod
    def get_last_request(cls):
        return cls.__last_request

    @classmethod
    def set_last_request(cls, val):
        cls.__last_request = val

    def get(self, url, params=None, **kwargs):
        if self.get_last_request() > 0:
            msecs_since_last = int(time.time() * 1000) - self.get_last_request()
            if msecs_since_last < constants.MUSICBRAINZ_DELAY:
                delay = constants.MUSICBRAINZ_DELAY - msecs_since_last
                settings.log('  %sms since last Musicbrainz-request, delay %sms' % (msecs_since_last, delay))
                xbmc.sleep(delay)
            else:
                settings.log('  %sms since last Musicbrainz-request, no delay' % msecs_since_last)
        else:
            settings.log('  No last Musicbrainz-request, no delay')
        result = requests.get(url, params, **kwargs)
        self.set_last_request(int(time.time() * 1000))
        return result


class RealNameFinder(ArtistAlbum):

    def find(self):
        if self.__class__.__name__ != 'RealNameFinder':
            raise NotImplementedError

        settings.log('    RealNameFinder starting, %s' % self, xbmc.LOGNOTICE)
        realname_result = RealNameResult()
        if not realname_result.has_any:
            realname_result = ITunesRealNameFinder.from_other(self).find()
        return realname_result


class ITunesRealNameFinder(RealNameFinder):

    def find(self):
        settings.log('      ITunesRealNameFinder starting, %s' % self, xbmc.LOGNOTICE)
        result = RealNameResult()
        if self.artist is not None:
            url = constants.APPLE_SERVLET
            params = dict(constants.APPLE_DEFAULT_PARAMS)
            if self.album is not None:
                params.update({'term': self.artist + ' ' + self.album, 'entity': 'album'})
            else:
                params.update({'term': self.artist, 'entity': 'musicArtist'})
            try:
                r = requests.get(url, params, headers={'user-agent': __settings__.getUserAgent()})
                # settings.log(r.url)
                json = r.json()
                if 'resultCount' in json and json['resultCount'] > 0:
                    wrapper_type = json['results'][0]['wrapperType']
                    if wrapper_type == 'artist':
                        result.artist = json['results'][0]['artistName']
                    if wrapper_type == 'collection':
                        result.artist = json['results'][0]['artistName']
                        result.album = json['results'][0]['collectionName']
                settings.log('      ITunesRealNameFinder result: %s' % result, xbmc.LOGNOTICE)
            except:
                settings.log('      ITunesRealNameFinder result: failed', xbmc.LOGWARNING)

        return result
