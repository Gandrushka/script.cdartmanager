import xbmc
import time
import requests
import constants
import utils
import xml.etree.ElementTree as ET

import xxx_musicbrainz

import settings
__settings__ = settings.Settings()


# Modules to find the MBID for an artist/album
class MBIDFinder:

    def __init__(self, artist_name, album_name=None):
        self.artist_name = artist_name
        self.album_name = album_name
        pass

    def find(self):
        if self.__class__.__name__ != "MBIDFinder":
            raise NotImplementedError

        settings.log("MBIDFinder starting, artist=%s, album=%s" % (self.artist_name, self.album_name))
        mbid_result = MBIDResult()
        if not mbid_result.has_result:
            pass
            # mbid_result = TadbMBIDFinder(self.artist_name, self.album_name).find()
        if not mbid_result.has_result:
            mbid_result = MusicbrainzMBIDFinder(self.artist_name, self.album_name).find()
        return mbid_result


class TadbMBIDFinder(MBIDFinder):

    def find(self):
        settings.log("TadbMBIDFinder starting, artist=%s, album=%s" % (self.artist_name, self.album_name))
        result = MBIDResult()
        if self.artist_name is not None:

            if self.album_name is not None:
                url = constants.TADB_ALBUM_SERVLET
                params = {'s': self.artist_name, 'a': self.album_name}
            else:
                url = constants.TADB_ARTIST_SERVLET
                params = {'s': self.artist_name}

            try:
                r = requests.get(url, params, headers={'user-agent': __settings__.getUserAgent()})
                json = r.json()
                if "artists" in json and json["artists"] is not None:
                    bestmatch = json["artists"][0]
                    if "strMusicBrainzID" in bestmatch and utils.is_mbid(bestmatch["strMusicBrainzID"]):
                        result.artist_mbid = bestmatch["strMusicBrainzID"]
                if "album" in json and json["album"] is not None:
                    bestmatch = json["album"][0]
                    if "strMusicBrainzID" in bestmatch and utils.is_mbid(bestmatch["strMusicBrainzID"]):
                        result.album_mbid = bestmatch["strMusicBrainzID"]
                    if "strMusicBrainzArtistID" in bestmatch and utils.is_mbid(bestmatch["strMusicBrainzArtistID"]):
                        result.artist_mbid = bestmatch["strMusicBrainzArtistID"]
                settings.log("TheAudioDB result: artist=%s, album=%s" % (result.artist_mbid, result.album_mbid))
            except:
                settings.log("TheAudioDB result: failed")
        return result


class MusicbrainzMBIDFinder(MBIDFinder):

    def find(self):

        settings.log("MusicbrainzMBIDFinder starting, artist=%s, album=%s" % (self.artist_name, self.album_name))
        result = MBIDResult()

        # if self.album_name is not None:
        #     musicbrainz_albuminfo, _ = xxx_musicbrainz.get_musicbrainz_album(self.album_name, self.artist_name, 0, 1)
        #     if "id" in musicbrainz_albuminfo and MBIDResult.is_mbid(musicbrainz_albuminfo["id"]):
        #         result.album_mbid = musicbrainz_albuminfo["id"]
        #     if "artist_id" in musicbrainz_albuminfo and MBIDResult.is_mbid(musicbrainz_albuminfo["artist_id"]):
        #         result.artist_mbid = musicbrainz_albuminfo["artist_id"]
        # else:
        #     _, artist_id, _ = xxx_musicbrainz.get_musicbrainz_artist_id(self.artist_name)
        #     if MBIDResult.is_mbid(artist_id):
        #         result.artist_mbid = artist_id
        # settings.log("Musicbrainz result: artist=%s, album=%s" % (result.artist_mbid, result.album_mbid))

        # elif self.artist_name is not None:

        if self.artist_name is not None:

            # Musicbrainz artist search
            if not result.has_result:
                url = constants.MUSICBRAINZ_ARTIST_SERVLET
                params = {'query': 'artist:"%s"' % self.artist_name, 'limit': 1}
                r = ThrottledMusicbrainzRequest().get(url, params, headers={'user-agent': __settings__.getUserAgent()})
                xml = ET.fromstring(r.text)
                if all(x in xml.tag for x in ["{", "}"]):
                    ns = xml.tag[xml.tag.find("{"):xml.tag.find("}") + 1]
                else:
                    ns = ""
                artist_element = xml.find(".//%sartist[@id]" % ns)
                if artist_element is not None and utils.is_mbid(artist_element.get("id", None)):
                    result.artist_mbid = artist_element.get("id")

            # Musicbrainz alias search
            if not result.has_result:
                url = constants.MUSICBRAINZ_ARTIST_SERVLET
                params = {'query': 'alias:"%s"' % self.artist_name, 'limit': 1}
                r = ThrottledMusicbrainzRequest().get(url, params, headers={'user-agent': __settings__.getUserAgent()})
                xml = ET.fromstring(r.text)
                if all(x in xml.tag for x in ["{", "}"]):
                    ns = xml.tag[xml.tag.find("{"):xml.tag.find("}") + 1]
                else:
                    ns = ""
                artist_element = xml.find(".//%sartist[@id]" % ns)
                if artist_element is not None and utils.is_mbid(artist_element.get("id", None)):
                    result.artist_mbid = artist_element.get("id")

        return result


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
                settings.log("%sms since last Musicbrainz-request, delay %sms" % (msecs_since_last, delay))
                xbmc.sleep(delay)
            else:
                settings.log("%sms since last Musicbrainz-request, no delay" % msecs_since_last)
        else:
            settings.log("No last Musicbrainz-request, no delay")

        result = requests.get(url, params, **kwargs)
        self.set_last_request(int(time.time() * 1000))
        return result


class MBIDResult:

    def __init__(self, artist_mbid=None, album_mbid=None):
        self.__artist_mbid = artist_mbid
        self.__album_mbid = album_mbid
        pass

    @property
    def has_result(self):
        return self.has_artist_mbid or self.has_album_mbid

    @property
    def artist_mbid(self):
        return self.__artist_mbid

    @artist_mbid.setter
    def artist_mbid(self, value):
        self.__artist_mbid = value

    @property
    def has_artist_mbid(self):
        return utils.is_mbid(self.artist_mbid)

    @property
    def album_mbid(self):
        return self.__album_mbid

    @album_mbid.setter
    def album_mbid(self, value):
        self.__album_mbid = value

    @property
    def has_album_mbid(self):
        return utils.is_mbid(self.album_mbid)
