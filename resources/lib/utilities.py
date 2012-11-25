import sys
import os
import chardet
import xbmc, xbmcvfs

__addon__     = sys.modules[ "__main__" ].__addon__
__addonname__ = sys.modules[ "__main__" ].__addonname__
__profile__   = sys.modules[ "__main__" ].__profile__
__cwd__       = sys.modules[ "__main__" ].__cwd__

CANCEL_DIALOG  = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
LYRIC_SCRAPER_DIR = os.path.join(__cwd__, "resources", "lib", "scrapers")

def _create_base_paths():
    """ creates the base folders """
    if ( not xbmcvfs.exists( __profile__.encode("utf-8") ) ):
        xbmcvfs.mkdirs( __profile__.encode("utf-8") )
_create_base_paths()

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode("utf-8")
    message = u'%s: %s' % (__addonname__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

def get_settings():
    settings = {}
    settings[ "search_embedded" ] = __addon__.getSetting( "search_embedded" ) == "true"
    settings[ "search_file" ] = __addon__.getSetting( "search_file" ) == "true"
    settings[ "save_lyrics" ] = __addon__.getSetting( "save_lyrics" ) == "true"
    settings[ "save_lyrics_path" ] = __addon__.getSetting( "save_lyrics_path" )
    if ( settings[ "save_lyrics_path" ] == "" ):
        settings[ "save_lyrics_path" ] = os.path.join( __profile__.encode("utf-8"), "lyrics" )
        __addon__.setSetting(id="save_lyrics_path", value=settings[ "save_lyrics_path" ])
    settings[ "save_artist_folder" ] = __addon__.getSetting( "save_artist_folder" ) == "true"
    settings[ "read_filename" ] = __addon__.getSetting( "read_filename" ) == "true"
    settings[ "read_filename_format" ] = __addon__.getSetting( "read_filename_format" )
    settings[ "read_subfolder" ] = __addon__.getSetting( "read_subfolder" ) == "true"
    settings[ "read_subfolder_path" ] = __addon__.getSetting( "read_subfolder_path" )
    return settings

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
    except IOError:
        return ""
