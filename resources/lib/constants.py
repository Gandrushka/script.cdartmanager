import xbmc

ADDON_ID = "script.cdartmanager-dev"
ADDON_BRANCH = "NG"

ADDON_FILENAME_SETTINGS = "settings.xml"
ADDON_DIRNAME_RESOURCES = "resources"

SKIN_FOLDER = "NG"

LOG_DEFAULTLEVEL = xbmc.LOGNOTICE
LOG_STARTUP_BORDER = "###########################################################"
LOG_STARTUP_LINE = "# %-55s #"
LOG_STARTUP_STATIC = ["", "This addon is yet another fork of the original", "cdART Manager by giftie, thanks to all contributors!"]

WORKDIR_TEMP_XML = "tempxml"
WORKDIR_TEMP_GFX = "tempgfx"

DB_VERSION = "3.0.3"
DB_VERSION_OLD = "2.7.8"
DB_VERSION_ANCIENT = "1.5.3"

DB_FILENAME = "l_cdart.db"
DB_FILENAME_UPDATE = "l_cdart." + DB_VERSION_OLD + ".db"
DB_FILENAME_JOURNAL = "l_cdart.db-journal"
DB_FILENAME_BACKUP = "l_cdart-%s.bak"

DS_DIR = "datastore"
DS_ARTISTS_FILE = "artists.json"
DS_ALBUMS_FILE = "albums.json"

FANARTTV_API_KEY = "e308cc6c6f76e502f98526f1694c62ac"
FANARTTV_SERVER = "http://webservice.fanart.tv"
FANARTTV_MUSIC_BASE_URL = "%(server)s/v3/music/%%(mbid)s?api_key=%(api_key)s" % {'server': FANARTTV_SERVER, 'api_key': FANARTTV_API_KEY}
FANARTTV_MUSIC_LATEST_URL = "%(server)s/v3/music/latest?api_key=%(api_key)s&date=%%(date_code)s" % {'server': FANARTTV_SERVER, 'api_key': FANARTTV_API_KEY}

TADB_API_KEY = "9982148621896198621597"
TADB_SERVER = "http://www.theaudiodb.com"
TADB_ARTIST_SERVLET = "%(server)s/api/v1/json/%(api_key)s/search.php" % {'server': TADB_SERVER, 'api_key': TADB_API_KEY}
TADB_ALBUM_SERVLET = "%(server)s/api/v1/json/%(api_key)s/searchalbum.php" % {'server': TADB_SERVER, 'api_key': TADB_API_KEY}

MUSICBRAINZ_DELAY = 1000
MUSICBRAINZ_SERVER = "http://musicbrainz.org"
MUSICBRAINZ_ARTIST_SERVLET = "%(server)s/ws/2/artist/" % {'server': MUSICBRAINZ_SERVER}
MUSICBRAINZ_ALBUM_SERVLET = "%(server)s/ws/2/release/" % {'server': MUSICBRAINZ_SERVER}
MUSICBRAINZ_DEFAULT_PARAMS = {'fmt': 'json', 'limit': 1}

MUSICBRAINZ_VA_MBID = "89ad4ac3-39f7-470e-963a-56509c546377"
MUSICBRAINZ_VA_SERVLET = "%(server)s/ws/2/artist/%(va)s" % {'server': MUSICBRAINZ_SERVER, 'va': MUSICBRAINZ_VA_MBID}
MUSICBRAINZ_VA_PARAMS = {'fmt': 'json', 'inc': 'aliases'}

APPLE_SERVER = "http://itunes.apple.com"
APPLE_SERVLET = "%(server)s/search" % {'server': APPLE_SERVER}
APPLE_DEFAULT_PARAMS = {"media": "music", "limit": 1}

COLORS = {"white": "FFFFFFFF", "blue": "FF0000FF", "cyan": "FF00FFFF", "violet": "FFEE82EE", "pink": "FFFF1493",
          "red": "FFFF0000", "green": "FF00FF00", "yellow": "FFFFFF00", "orange": "FFFF4500"}

ART_FILENAME_ALBUM_COVER = "folder.jpg"
ART_FILENAME_ALBUM_CDART = "cdart.png"