# -*- coding: utf-8 -*-

import xbmc
import sys, os, re
from urllib import quote_plus
from traceback import print_exc

try:
    from sqlite3 import dbapi2 as sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3
    
__language__      = sys.modules[ "__main__" ].__language__
__scriptname__    = sys.modules[ "__main__" ].__scriptname__
__scriptID__      = sys.modules[ "__main__" ].__scriptID__
__version__       = sys.modules[ "__main__" ].__version__
__addon__         = sys.modules[ "__main__" ].__addon__
addon_db          = sys.modules[ "__main__" ].addon_db
addon_work_folder = sys.modules[ "__main__" ].addon_work_folder
BASE_RESOURCE_PATH= sys.modules[ "__main__" ].BASE_RESOURCE_PATH

#sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

from utils import get_html_source, unescape, log

artist_url = '''http://musicbrainz.org/ws/2/artist/?query=artist:"%s"&limit=%d'''
alias_url = '''http://musicbrainz.org/ws/2/artist/?query=alias:"%s"&limit=%d'''
release_group_url_nosingles = '''http://musicbrainz.org/ws/2/release-group/?query="%s"%s AND artist:"%s" NOT type:single&limit=%d'''
release_group_url_using_release_name = '''http://musicbrainz.org/ws/2/release-group/?query=release:"%s"%s AND artist:"%s"&limit=%d'''
release_group_url_singles = '''http://musicbrainz.org/ws/2/release-group/?query="%s"%s AND artist:"%s"&limit=%d'''
release_group_url_nosingles_alias = '''http://musicbrainz.org/ws/2/release-group/?query="%s"%s AND alias:"%s" NOT type:single&limit=%d'''
release_group_url_using_release_name_alias = '''http://musicbrainz.org/ws/2/release-group/?query=release:"%s"%s AND alias:"%s"&limit=%d'''
release_group_url_singles_alias = '''http://musicbrainz.org/ws/2/release-group/?query="%s"%s AND alias:"%s"&limit=%d'''
release_group_url_release_mbid = '''http://musicbrainz.org/ws/2/release-group/?release=%s'''
release_groups_url_artist_mbid = '''http://musicbrainz.org/ws/2/release-group/?artist="%s"'''
artist_id_check = '''http://www.musicbrainz.org/ws/2/artist/%s'''
release_group_id_check = '''http://www.musicbrainz.org/ws/2/release-group/%s'''

def split_album_info( album_result, index ):
    album = {}
    try:
        album["artist"] = album_result[ index ].releaseGroup.artist.name
        album["artist_id"] = ( album_result[ index ].releaseGroup.artist.id ).replace( "http://musicbrainz.org/artist/", "" )
        album["id"] = ( album_result[ index ].releaseGroup.id ).replace( "http://musicbrainz.org/release-group/", "" )
        album["title"] = album_result[ index ].releaseGroup.title
    except:
        album["artist"] = ""
        album["artist_id"] = ""
        album["id"] = ""
        album["title"] = ""
    return album

def get_musicbrainz_release_group( release_mbid ):
    """ Retrieves the MusicBrainz Release Group MBID from a given release MBID
        
        Use:
            release_groupmbid = get_musicbrainz_release_group( release_mbid )
        
        release_mbid - valid release mbid
    """
    log( "Retrieving MusicBrainz Release Group MBID from Album Release MBID", xbmc.LOGDEBUG )
    url = release_group_url_release_mbid % quote_plus( release_mbid )
    mbid = ""
    htmlsource = get_html_source( url, release_mbid, True )
    match = re.search( '''<release-group(.*?)</release-group>''', htmlsource )
    if match:
        mbid_match = re.search( '''<release-group id="(.*?)"(?:.*?)">''', htmlsource)
        if not mbid_match:
            mbid_match = re.search( '''<release-group (?:.*?)id="(.*?)">''', htmlsource )
        if mbid_match:
            mbid = mbid_match.group( 1 )
    xbmc.sleep( 900 )
    return mbid

def get_musicbrainz_album( album_title, artist, e_count, limit=1, with_singles=False, by_release=False, use_alias=False ):
    """ Retrieves information for Album from MusicBrainz using provided Album title and Artist name. 
        
        Use:
            album, albums = get_musicbrainz_album( album_title, artist, e_count, limit, with_singles, by_release )
        
        album_title  - the album title(must be unicode)
        artist       - the artist's name(must be unicode)
        e_count      - used internally(should be set to 0)
        limit        - limit the number of responses
        with_singles - set to True to look up single releases at the same time
        by_release   - use release name for search
    """
    match_within = "~2"
    album = {}
    albums = []
    count = e_count
    album["score"] = ""
    album["id"] = ""
    album["title"] = ""
    album["artist"] = ""
    album["artist_id"] = ""
    log( "Artist: %s" % artist, xbmc.LOGDEBUG )
    log( "Album: %s" % album_title, xbmc.LOGDEBUG )
    artist = artist.replace('"','?')
    album_title = album_title.replace('"','?')
    if limit == 1:
        if not with_singles and not by_release and not use_alias:
            log( "Retrieving MusicBrainz Info - Checking by Artist - Not including Singles", xbmc.LOGDEBUG )
            url = release_group_url_nosingles % ( quote_plus( album_title.encode("utf-8") ), match_within, quote_plus( artist.encode("utf-8") ), limit )
        elif not with_singles and not by_release and use_alias:
            log( "Retrieving MusicBrainz Info - Checking by Alias - Not including Singles", xbmc.LOGDEBUG )
            url = release_group_url_nosingles_alias % ( quote_plus( album_title.encode("utf-8") ), match_within, quote_plus( artist.encode("utf-8") ), limit )
        elif not by_release and not use_alias:
            log( "Retrieving MusicBrainz Info - Checking by Artist - Including Singles", xbmc.LOGDEBUG )
            url = release_group_url_singles % ( quote_plus( album_title.encode("utf-8") ), match_within, quote_plus( artist.encode("utf-8") ), limit )
        elif not by_release and use_alias:
            log( "Retrieving MusicBrainz Info - Checking by Alias - Including Singles", xbmc.LOGDEBUG )
            url = release_group_url_singles_alias % ( quote_plus( album_title.encode("utf-8") ), match_within, quote_plus( artist.encode("utf-8") ), limit )
        elif not with_singles and not use_alias:
            log( "Retrieving MusicBrainz Info - Checking by Artist - Using Release Name", xbmc.LOGDEBUG )
            url = release_group_url_using_release_name % ( quote_plus( album_title.encode("utf-8") ), match_within, quote_plus( artist.encode("utf-8") ), limit )
        elif not with_singles and use_alias:
            log( "Retrieving MusicBrainz Info - Checking by Alias - Using Release Name", xbmc.LOGDEBUG )
            url = release_group_url_using_release_name_alias % ( quote_plus( album_title.encode("utf-8") ), match_within, quote_plus( artist.encode("utf-8") ), limit )
        htmlsource = get_html_source( url, "", False )
        match = re.search( '''<release-group(.*?)</release-group>''', htmlsource )
        if match:
            try:
                mbid = re.search( '''<release-group id="(.*?)"(?:.*?)">''', htmlsource)
                if not mbid:
                    mbid = re.search( '''<release-group (?:.*?)id="(.*?)">''', htmlsource )
                mbtitle = re.search( '''<title>(.*?)</title>''', htmlsource)
                mbartist = re.search( '''<name>(.*?)</name>''', htmlsource)
                mbartistid = re.search( '''<artist id="(.*?)">''', htmlsource)
                album["id"] = mbid.group(1)
                album["title"] = mbtitle.group(1)
                album["artist"] = mbartist.group(1)
                album["artist_id"] = mbartistid.group(1)
            except:
                pass            
        if not album["id"]:
            if not with_singles and not by_release and not use_alias:
                log( "No releases found on MusicBrainz, Checking by Artist Alias", xbmc.LOGDEBUG )
                xbmc.sleep( 900 ) # sleep for allowing proper use of webserver
                album, albums = get_musicbrainz_album( album_title, artist, 0, limit, False, False, True ) # try again by using artist alias
            elif use_alias and not with_singles and not by_release:
                log( "No releases found on MusicBrainz, Checking by Release name", xbmc.LOGDEBUG )
                xbmc.sleep( 900 ) # sleep for allowing proper use of webserver
                album, albums = get_musicbrainz_album( album_title, artist, 0, limit, False, True, False ) # try again by using release name
            elif by_release and not with_singles and not use_alias:
                log( "No releases found on MusicBrainz, Checking by Release name and Artist Alias", xbmc.LOGDEBUG )
                xbmc.sleep( 900 ) # sleep for allowing proper use of webserver
                album, albums = get_musicbrainz_album( album_title, artist, 0, limit, False, True, True ) # try again by using release name and artist alias
            elif by_release and not with_singles and use_alias:
                log( "No releases found on MusicBrainz, checking singles", xbmc.LOGDEBUG )
                xbmc.sleep( 900 ) # sleep for allowing proper use of webserver
                album, albums = get_musicbrainz_album( album_title, artist, 0, limit, True, False, False ) # try again with singles
            elif with_singles and not use_alias and not by_release:
                log( "No releases found on MusicBrainz, checking singles and Artist Alias", xbmc.LOGDEBUG )
                xbmc.sleep( 900 ) # sleep for allowing proper use of webserver
                album, albums = get_musicbrainz_album( album_title, artist, 0, limit, True, False, True ) # try again with singles and artist alias
            else:
                xbmc.sleep( 900 )
                log( "No releases found on MusicBrainz.", xbmc.LOGDEBUG )
                album["artist"], album["artist_id"], sort_name = get_musicbrainz_artist_id( artist )
            
    else:
        match_within = "~4"
        url = release_group_url_singles % ( quote_plus( album_title.encode("utf-8") ), match_within, quote_plus( artist.encode("utf-8") ), limit )
        htmlsource = get_html_source( url, "", False )
        match = re.findall( '''<release-group(.*?)</release-group>''', htmlsource )
        if match:
            for item in match:
                album = {}
                album["score"] = ""
                album["id"] = ""
                album["title"] = ""
                album["artist"] = ""
                album["artist_id"] = ""
                try:
                    mbscore = re.search( '''score="(.*?)"''', item)
                    mbid = re.search( '''<release-group id="(.*?)"(?:.*?)">''', item)
                    if not mbid:
                        mbid = match = re.search( '''<release-group (?:.*?)id="(.*?)">''', htmlsource )
                    mbtitle = re.search( '''<title>(.*?)</title>''', item)
                    mbartist = re.search( '''<name>(.*?)</name>''', item)
                    mbartistid = re.search( '''<artist id="(.*?)">''', item)
                    album["score"] = mbscore.group(1)
                    album["id"] = mbid.group(1)
                    album["title"] = unescape( mbtitle.group(1) )
                    album["artist"] = unescape( mbartist.group(1) )
                    album["artist_id"] = mbartistid.group(1)
                    log( "Score     : %s" % album["score"], xbmc.LOGDEBUG )
                    log( "Title     : %s" % album["title"], xbmc.LOGDEBUG )
                    log( "Id        : %s" % album["id"], xbmc.LOGDEBUG )
                    log( "Artist    : %s" % album["artist"], xbmc.LOGDEBUG )
                    log( "Artist ID : %s" % album["artist_id"], xbmc.LOGDEBUG )
                    albums.append(album)
                except:
                    print_exc()
                
        else:
            pass
    xbmc.sleep( 910 ) # sleep for allowing proper use of webserver
    return album, albums

def get_musicbrainz_artists( artist_search, limit=1 ):
    try:
        log( "Artist: %s" % artist_search, xbmc.LOGDEBUG )
    except:
        log( "Artist: %s" % repr(artist_search), xbmc.LOGDEBUG )
    score = ""
    name = ""
    id = ""
    sortname = ""
    artists = []
    url = artist_url % ( quote_plus( artist_search.encode("utf-8") ), limit )
    htmlsource = get_html_source( url, "", False)
    match = re.findall( '''<artist(.*?)</artist>''', htmlsource )
    if match:
        for item in match:
            artist = {}
            artist["score"] = ""
            artist["name"] = ""
            artist["id"] = ""
            artist["sortname"] = ""
            score_match = re.search( '''score="(.*?)"''', item )
            name_match = re.search( '''<name>(.*?)</name>''', item )
            id_match = re.search( '''<artist id="(.*?)"(?:.*?)>''', htmlsource )
            if not id_match:
                id_match = re.search( '''<artist (?:.*?)id="(.*?)">''', htmlsource )
            sort_name_match = re.search( '''<sort-name>(.*?)</sort-name>''', item )
            if score_match:
                artist["score"] = score_match.group(1)
            if name_match:
                artist["name"] = name_match.group(1)
            if id_match:
                artist["id"] = id_match.group(1)
            if sort_name_match:
                artist["sortname"] = sort_name_match.group(1)
            log( "Score     : %s" % artist["score"], xbmc.LOGDEBUG )
            log( "Id        : %s" % artist["id"], xbmc.LOGDEBUG )
            log( "Name      : %s" % artist["name"], xbmc.LOGDEBUG )
            log( "Sort Name : %s" % artist["sortname"], xbmc.LOGDEBUG )
        artists.append(artist)
    else:
        log( "No Artist ID found for Artist: %s" % repr( artist_search ), xbmc.LOGDEBUG )
    return artists

def get_musicbrainz_artist_id( artist, limit=1, alias = False ):
    name = ""
    id = ""
    sortname = ""
    if not alias:
        url = artist_url % ( quote_plus( artist.encode("utf-8") ), limit )
    else:
        url = alias_url % ( quote_plus( artist.encode("utf-8") ), limit )
    htmlsource = get_html_source( url, "", False)
    match = re.search( '''<artist(.*?)</artist>''', htmlsource )
    if match:
        score_match = re.search( '''score="(.*?)"''', htmlsource )
        name_match = re.search( '''<name>(.*?)</name>''', htmlsource )
        id_match = re.search( '''<artist id="(.*?)"(?:.*?)>''', htmlsource )
        if not id_match:
            id_match = re.search( '''<artist (?:.*?)id="(.*?)">''', htmlsource )
        sort_name_match = re.search( '''<sort-name>(.*?)</sort-name>''', htmlsource )
        
        if score_match:
            score = score_match.group(1)
        if name_match:
            name = name_match.group(1)
        if id_match:
            id = id_match.group(1)
        if sort_name_match:
            sortname = sort_name_match.group(1)
        log( "Score     : %s" % score, xbmc.LOGDEBUG )
        log( "Id        : %s" % id, xbmc.LOGDEBUG )
        log( "Name      : %s" % name, xbmc.LOGDEBUG )
        log( "Sort Name : %s" % sortname, xbmc.LOGDEBUG )
        xbmc.sleep( 900 )
    else:
        xbmc.sleep( 910 ) # sleep for allowing proper use of webserver
        if not alias:
            log( "No Artist ID found trying aliases: %s" % artist, xbmc.LOGDEBUG )
            name, id, sortname = get_musicbrainz_artist_id( artist, limit, True )
        else:
            log( "No Artist ID found for Artist: %s" % artist, xbmc.LOGDEBUG )
    return name, id, sortname

def update_musicbrainzid( type, info ):
    log( "Updating MusicBrainz ID", xbmc.LOGDEBUG )
    artist_id = ""
    try:
        if type == "artist":  # available data info["local_id"], info["name"], info["distant_id"]
            name, artist_id, sortname = get_musicbrainz_artist_id( info["name"] )
            conn = sqlite3.connect(addon_db)
            c = conn.cursor()
            c.execute('UPDATE alblist SET musicbrainz_artistid="%s" WHERE artist="%s"' % (artist_id, info["name"]) )
            try:
                c.execute('UPDATE lalist SET musicbrainz_artistid="%s" WHERE name="%s"' % (artist_id, info["name"]) )
            except:
                pass
            conn.commit
            c.close()
        if type == "album":
            album_id = get_musicbrainz_album( info["title"], info["artist"], 0 )["id"] 
            conn = sqlite3.connect(addon_db)
            c = conn.cursor()
            c.execute("""UPDATE alblist SET musicbrainz_albumid='%s' WHERE title='%s'""" % (album_id, info["title"]) )
            conn.commit
            c.close()
    except:
        print_exc()
    return artist_id
    
def mbid_check( database_mbid, type ):
    log( "Looking up %s MBID. Current MBID: %s" % ( type, database_mbid ), xbmc.LOGNOTICE )
    new_mbid = ""
    mbid_match = False
    if type == "release-group":
        url = release_group_id_check % database_mbid
    elif type == "artist":
        url = artist_id_check % database_mbid
    htmlsource = get_html_source( url, "", False)
    if type == "release-group":
        match = re.search( '''<release-group id="(.*?)"(?:.*?)>''', htmlsource )
        if match:
            new_mbid = match.group( 1 )
        else:
            match = re.search( '''<release-group (?:.*?)id="(.*?)">''', htmlsource )
            if match:
                new_mbid = match.group( 1 )
            else:
                match = re.search( '''<release-group ext:score=(?:.*?)id="(.*?)">''', htmlsource )
                if match:
                    new_mbid = match.group( 1 )
        if new_mbid == database_mbid:
            mbid_match = True
        else:
            mbid_match = False
    elif type == "artist":
        match = re.search( '''<artist id="(.*?)"(?:.*?)>''', htmlsource )
        if match:
            new_mbid = match.group( 1 )
        else:
            match = re.search( '''<artist(?:.*?)id="(.*?)">''', htmlsource )
            if match:
                new_mbid = match.group( 1 )
        if new_mbid == database_mbid:
            mbid_match = True
        else:
            mbid_match = False
    else:
        pass
    log( "Current MBID: %s    New MBID: %s" % ( database_mbid, new_mbid ), xbmc.LOGDEBUG )
    if mbid_match:
        log( "MBID is current. No Need to change", xbmc.LOGDEBUG )
    else:
        log( "MBID is not current. Need to change", xbmc.LOGDEBUG )
    return mbid_match, new_mbid

