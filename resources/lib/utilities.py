import sys
import os
import re
import chardet
import unicodedata
import xbmc, xbmcvfs, xbmcgui
if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__     = sys.modules[ "__main__" ].__addon__
__addonname__ = sys.modules[ "__main__" ].__addonname__
__profile__   = sys.modules[ "__main__" ].__profile__
__cwd__       = sys.modules[ "__main__" ].__cwd__

CANCEL_DIALOG = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
ACTION_OSD = ( 122, )
LYRIC_SCRAPER_DIR = os.path.join(__cwd__, "resources", "lib", "culrcscrapers")
WIN = xbmcgui.Window( 10000 )

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode("utf-8")
    message = u'%s: %s' % (__addonname__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

def deAccent(str):
    return unicodedata.normalize('NFKD', unicode(str, 'utf-8'))

def get_textfile(filepath):
    try:
        file = xbmcvfs.File( filepath )
        data = file.read()
        file.close()
        # Detect text encoding
        enc = chardet.detect(data)
        if (enc['encoding'] == 'utf-8'):
            return data
        else:
            return unicode( data, enc['encoding'] ).encode( "utf-8")
    except UnicodeDecodeError:
        return data
    except:
        return None

def get_artist_from_filename(filename):
    try:
        artist = ''
        title = ''
        basename = os.path.basename( filename )
        # Artist - title.ext
        if ( __addon__.getSetting( "read_filename_format" ) == "0" ):
            artist = basename.split( "-", 1 )[ 0 ].strip()
            title = os.path.splitext( basename.split( "-", 1 )[ 1 ].strip() )[ 0 ]
        # Artist/Album/title.ext or Artist/Album/Track title.ext
        elif ( __addon__.getSetting( "read_filename_format" ) in ( "1", "2", ) ):
            artist = os.path.basename( os.path.split( os.path.split( filename )[ 0 ] )[ 0 ] )
            # Artist/Album/title.ext
            if ( __addon__.getSetting( "read_filename_format" ) == "1" ):
                title = os.path.splitext( basename )[ 0 ]
            # Artist/Album/Track title.ext
            elif ( __addon__.getSetting( "read_filename_format" ) == "2" ):
                title = os.path.splitext( basename )[ 0 ].split( " ", 1 )[ 1 ]
    except:
        # invalid format selected
        log( "failed to get artist and title from filename" )
    return artist, title

class Lyrics:
    def __init__(self):
        self.song = Song()
        self.lyrics = ""
        self.source = ""
        self.list = None
        self.lrc = False

class Song:
    def __init__(self):
        self.artist = ""
        self.title = ""
        self.filepath = ""
        self.analyze_safe = True

    def __str__(self):
        return "Artist: %s, Title: %s" % ( self.artist, self.title)

    def __cmp__(self, song):
        if (self.artist != song.artist):
            return cmp(deAccent(self.artist), deAccent(song.artist))
        else:
            return cmp(deAccent(self.title), deAccent(song.title))

    def sanitize(self, str):
        return str.replace( "\\", "_" ).replace( "/", "_" ).replace(":","_").replace("?","_").replace("!","_").strip('.')

    def path1(self, lrc):
        if lrc:
            ext = '.lrc'
        else:
            ext = '.txt'
        if ( __addon__.getSetting( "save_filename_format" ) == "0" ):
            return unicode( os.path.join( __addon__.getSetting( "save_lyrics_path" ), self.sanitize(self.artist), self.sanitize(self.title) + ext ), "utf-8" )
        else:
            return unicode( os.path.join( __addon__.getSetting( "save_lyrics_path" ), self.sanitize(self.artist) + " - " + self.sanitize(self.title) + ext ), "utf-8" )

    def path2(self, lrc):
        if lrc:
            ext = '.lrc'
        else:
            ext = '.txt'
        dirname = os.path.dirname(self.filepath)
        basename = os.path.basename(self.filepath)
        filename = basename.rsplit( ".", 1 )[ 0 ]
        if ( __addon__.getSetting( "save_subfolder" ) == "true" ):
            return unicode( os.path.join( dirname, __addon__.getSetting( "save_subfolder_path" ), filename + ext ), "utf-8" )
        else:
            return unicode( os.path.join( dirname, filename + ext ), "utf-8" )


    @staticmethod
    def current():
        song = Song.by_offset(0)

        if not song.artist and not xbmc.getInfoLabel("MusicPlayer.TimeRemaining"):
            # no artist and infinite playing time ? We probably listen to a radio
            # which usually set the song title as "Artist - Title" (via ICY StreamTitle)
            sep = song.title.find("-")
            if sep > 1:
                song.artist = song.title[:sep - 1].strip()
                song.title = song.title[sep + 1:].strip()
                # The title in the radio often contains some additional
                # bracketed information at the end:
                #  Radio version, short version, year of the song...
                # It often disturbs the lyrics search so we remove it
                song.title = re.sub(r'\([^\)]*\)$', '', song.title)
        return song

    @staticmethod
    def next():
        song = Song.by_offset(1)
        if song.artist != '' and song.title != '':
            return song

    @staticmethod
    def by_offset(offset = 0):
        song = Song()
        if offset > 0:
            offset_str = ".offset(%i)" % offset
            try:
                pos = int(xbmc.getInfoLabel('MusicPlayer.PlaylistPosition')) + offset
                json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.GetItems", "params": {"properties": ["file"], "playlistid": 0, "limits": {"start": %i, "end": %i} }, "id": 1}' % (pos-1, pos))
                json_query = unicode(json_query, 'utf-8', errors='ignore')
                json_response = simplejson.loads(json_query)
                song.filepath = json_response['result']['items'][0]['file'].encode('utf-8')
            except:
                song.filepath = ""
        else:
            offset_str = ""
            song.filepath = xbmc.getInfoLabel('Player.Filenameandpath')
        song.title = xbmc.getInfoLabel( "MusicPlayer%s.Title" % offset_str)
        song.artist = xbmc.getInfoLabel( "MusicPlayer%s.Artist" % offset_str)
        if ( song.filepath and ( (not song.title) or (not song.artist) or (__addon__.getSetting( "read_filename" ) == "true") ) ):
            song.artist, song.title = get_artist_from_filename( song.filepath )
        if __addon__.getSetting( "clean_title" ) == "true":
            song.title = re.sub(r'\([^\)]*\)$', '', song.title)
        
        #Check if analyzing the stream is discouraged
        do_not_analyze = xbmc.getInfoLabel('MusicPlayer.Property(do_not_analyze)')
        if do_not_analyze == 'true':
            song.analyze_safe = False
        
        return song
