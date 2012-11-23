import sys
import os
import chardet
import xbmc, xbmcvfs

__addon__     = sys.modules[ "__main__" ].__addon__
__addonname__ = sys.modules[ "__main__" ].__addonname__
__profile__   = sys.modules[ "__main__" ].__profile__

# base paths
BASE_DATA_PATH = sys.modules[ "__main__" ].__profile__

def _create_base_paths():
    """ creates the base folders """
    if ( not xbmcvfs.exists( BASE_DATA_PATH.decode("utf-8") ) ):
        xbmcvfs.mkdirs( BASE_DATA_PATH.decode("utf-8") )
_create_base_paths()

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode("utf-8")
    message = u'%s: %s' % (__addonname__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

def get_settings():
    settings = {}
    settings[ "scraper" ] = __addon__.getSetting( "scraper" )
    settings[ "save_lyrics" ] = __addon__.getSetting( "save_lyrics" ) == "true"
    settings[ "lyrics_path" ] = __addon__.getSetting( "lyrics_path" )
    if ( settings[ "lyrics_path" ] == "" ):
        settings[ "lyrics_path" ] = os.path.join( BASE_DATA_PATH, "lyrics" )
        __addon__.setSetting(id="lyrics_path", value=settings[ "lyrics_path" ])
    settings[ "smooth_scrolling" ] = __addon__.getSetting( "smooth_scrolling" ) == "true"
    settings[ "use_filename" ] = __addon__.getSetting( "use_filename" ) == "true"
    settings[ "filename_format" ] = __addon__.getSetting( "filename_format" )
    settings[ "artist_folder" ] = __addon__.getSetting( "artist_folder" ) == "true"
    settings[ "subfolder" ] = __addon__.getSetting( "subfolder" ) == "true"
    settings[ "subfolder_name" ] = __addon__.getSetting( "subfolder_name" )
    return settings

def get_textfile(filepath):
    try:
        if (not xbmcvfs.exists(filepath)):
            return ""
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
