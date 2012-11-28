#-*- coding: UTF-8 -*-
import sys
import os
import re
import thread
import xbmc, xbmcgui, xbmcvfs
from threading import Timer
from utilities import *
from embedlrc import *

__addon__     = sys.modules[ "__main__" ].__addon__
__profile__   = sys.modules[ "__main__" ].__profile__
__language__  = sys.modules[ "__main__" ].__language__

class GUI( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )

    def onInit( self ):
        self.setup_all()

    def setup_all( self ):
        self.setup_variables()
        self.settings = get_settings()
        self.get_scraper_list()
        self.getMyPlayer()

    def get_scraper_list( self ):
        for scraper in os.listdir(LYRIC_SCRAPER_DIR):
            if os.path.isdir(os.path.join(LYRIC_SCRAPER_DIR, scraper)) and __addon__.getSetting( scraper ) == "true":
                exec ( "from scrapers.%s import lyricsScraper as lyricsScraper_%s" % (scraper, scraper))
                exec ( "self.scrapers.append([lyricsScraper_%s.__priority__,lyricsScraper_%s.LyricsFetcher(),lyricsScraper_%s.__title__,lyricsScraper_%s.__lrc__])" % (scraper, scraper, scraper, scraper))
                self.scrapers.sort()

    def setup_variables( self ):
        self.lock = thread.allocate_lock()
        self.timer = None
        self.allowtimer = True
        self.songfile = None
        self.controlId = -1
        self.pOverlay = []
        self.scrapers = []

    def refresh(self):
        self.lock.acquire()
        try:
            #May be XBMC is not playing any media file
            cur_time = xbmc.Player().getTime()
            nums = self.getControl( 110 ).size()
            pos = self.getControl( 110 ).getSelectedPosition()
            if (cur_time < self.pOverlay[pos][0]):
                while (pos > 0 and self.pOverlay[pos - 1][0] > cur_time):
                    pos = pos -1
            else:
                while (pos < nums - 1 and self.pOverlay[pos + 1][0] < cur_time):
                    pos = pos +1
                if (pos + 5 > nums - 1):
                    self.getControl( 110 ).selectItem( nums - 1 )
                else:
                    self.getControl( 110 ).selectItem( pos + 5 )
            self.getControl( 110 ).selectItem( pos )
            self.setFocus( self.getControl( 110 ) )
            if (self.allowtimer and cur_time < self.pOverlay[nums - 1][0]):
                waittime = self.pOverlay[pos + 1][0] - cur_time
                self.timer = Timer(waittime, self.refresh)
                self.timer.start()
            self.lock.release()
        except:
            self.lock.release()

    def show_control( self, controlId ):
        self.getControl( 100 ).setVisible( controlId == 100 )
        self.getControl( 110 ).setVisible( controlId == 110 )
        xbmc.sleep( 5 )
        if controlId == 110:
            try:
                self.setFocus( self.getControl( controlId + 1 ) )
            except:
                self.setFocus( self.getControl( controlId ) )
        elif controlId == 100:
            try:
                self.setFocus( self.getControl( 605 ) )
            except:
                pass

    def find_lyrics(self, artist, song):
        self.reset_controls()
        self.menu_items = None
        self.source = ''
        xbmc.sleep( 60 )
        # search embedded lrc lyrics
        self.lrc = True
        if ( self.settings[ "search_embedded" ] ):
            lyrics = getEmbedLyrics(xbmc.getInfoLabel('Player.Filenameandpath').decode("utf-8"))
            if ( lyrics ):
                log('found embedded lrc lyrics')
                self.source = __language__( 30002 )
                self.show_lyrics( lyrics )
                return
        # search lrc lyrics in file
        if ( self.settings[ "search_file" ] ):
            lyrics = self.get_lyrics_from_file(artist, song, True)
            if ( lyrics ):
                log('found lrc lyrics from file')
                self.source = __language__( 30000 )
                self.show_lyrics( lyrics )
                return
        # search lrc lyrics by scrapers
        for self.scraper in self.scrapers:
            if self.scraper[3]:
                lyrics = self.scraper[1].get_lyrics( artist, song )
                if ( lyrics ):
                    log('found lrc lyrics online')
                    self.source = self.scraper[2]
                    self.show_lyrics( lyrics, True )
                    return

        # search embedded txt lyrics
        self.lrc = False
        if ( self.settings[ "search_embedded" ] ):
            lyrics = xbmc.getInfoLabel( "MusicPlayer.Lyrics" )
            if lyrics:
                log('found embedded txt lyrics')
                self.source = __language__( 30002 )
                self.show_lyrics( lyrics )
                return
        # search txt lyrics in file
        if ( self.settings[ "search_file" ] ):
            lyrics = self.get_lyrics_from_file(artist, song, False)
            if ( lyrics ):
                log('found txt lyrics from file')
                self.source = __language__( 30000 )
                self.show_lyrics( lyrics )
                return
        # search txt lyrics by scrapers
        for self.scraper in self.scrapers:
            if not self.scraper[3]:
                lyrics = self.scraper[1].get_lyrics( artist, song )
                if ( lyrics ):
                    log('found txt lyrics online')
                    self.source = self.scraper[2]
                    self.show_lyrics( lyrics, True )
                    return
        log('no lyrics found')
        self.getControl( 100 ).setText( __language__( 30001 ) )
        self.show_control( 100 )

    def get_lyrics_from_list( self, item ):
        lyrics = self.scraper[1].get_lyrics_from_list( self.menu_items[ item ] )
        self.getControl( 110 ).reset()        
        self.show_lyrics( lyrics, True )

    def get_lyrics_from_file( self, artist, song, getlrc ):
        if getlrc:
            ext = '.lrc'
        else:
            ext = '.txt'
        path = xbmc.getInfoLabel('Player.Filenameandpath')
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        filename = basename.rsplit( ".", 1 )[ 0 ]
        if ( self.settings[ "read_subfolder" ] ):
            self.song_path = unicode( os.path.join( dirname, self.settings[ "read_subfolder_path" ], filename + ext ), "utf-8" )
        else:
            self.song_path = unicode( os.path.join( dirname, filename + ext ), "utf-8" )
        if xbmcvfs.exists(self.song_path):
            return get_textfile( self.song_path )
        if ( self.settings[ "save_artist_folder" ] ):
            self.song_path = unicode( os.path.join( self.settings[ "save_lyrics_path" ], artist.replace( "\\", "_" ).replace( "/", "_" ), song.replace( "\\", "_" ).replace( "/", "_" ) + ext ), "utf-8" )
        else:
            self.song_path = unicode( os.path.join( self.settings[ "save_lyrics_path" ], artist.replace( "\\", "_" ).replace( "/", "_" ) + " - " + song.replace( "\\", "_" ).replace( "/", "_" ) + ext ), "utf-8" )
        if xbmcvfs.exists(self.song_path):
            return get_textfile( self.song_path )
        else:
            return None

    def save_lyrics_to_file( self, lyrics ):
        try:
            if ( not xbmcvfs.exists( os.path.dirname( self.song_path ) ) ):
                xbmcvfs.mkdirs( os.path.dirname( self.song_path ) )
            base_file = os.path.splitext( self.song_path )[0]
            if self.lrc:
                self.song_path = base_file + '.lrc'
            else:
                self.song_path = base_file + '.txt'
            if not isinstance (lyrics,str):
                lyrics = lyrics.encode('utf-8')

# xbmcvfs.File().write() corrupts files
# disable it until the bug is fixed
# http://trac.xbmc.org/ticket/13545
#            lyrics_file = xbmcvfs.File( self.song_path, "w" )
#            lyrics_file.write( lyrics )
#            lyrics_file.close()

            tmp_name = os.path.join(__profile__.encode("utf-8"), 'lyrics.tmp')
            tmp_file = open(tmp_name , "w" )
            tmp_file.write( lyrics )
            tmp_file.close()
            xbmcvfs.copy(tmp_name, self.song_path)
            xbmcvfs.delete(tmp_name)
            return True
        except:
            log( "failed to save lyrics" )
            return False

    def show_lyrics( self, lyrics, save=False ):
        self.getControl( 200 ).setLabel( self.source )
        if self.lrc:
            self.parser_lyrics( lyrics )
            for time, line in self.pOverlay:
                self.getControl( 110 ).addItem( line )
        else:
            splitLyrics = lyrics.splitlines()
            for x in splitLyrics:
               self.getControl( 110 ).addItem( x )
        self.getControl( 110 ).selectItem( 0 )
        self.show_control( 110 )
        if ( self.settings[ "save_lyrics" ] and save ):
            success = self.save_lyrics_to_file( lyrics )
        if self.lrc:
            if (self.allowtimer and self.getControl( 110 ).size() > 1):
                self.refresh()

    def parser_lyrics( self, lyrics):
        self.pOverlay = []
        tag = re.compile('\[(\d+):(\d\d)(\.\d+|)\]')
        lyrics = lyrics.replace( "\r\n" , "\n" )
        sep = "\n"
        for x in lyrics.split( sep ):
            match1 = tag.match( x )
            times = []
            if ( match1 ):
                while ( match1 ):
                    times.append( float(match1.group(1)) * 60 + float(match1.group(2)) )
                    y = 5 + len(match1.group(1)) + len(match1.group(3))
                    x = x[y:]
                    match1 = tag.match( x )
                for time in times:
                    self.pOverlay.append( (time, x) )
        self.pOverlay.sort( cmp=lambda x,y: cmp(x[0], y[0]) )

    def reset_controls( self ):
        self.getControl( 100 ).reset()
        self.getControl( 110 ).reset()
        self.getControl( 200 ).setLabel('')

    def exit_script( self ):
        self.lock.acquire()
        try:
            self.timer.cancel()
        except:
            pass
        self.allowtimer = False
        self.lock.release()
        self.close()

    def onFocus( self, controlId ):
        self.controlId = controlId

    def onAction( self, action ):
        actionId = action.getId()
        if ( actionId in CANCEL_DIALOG ):
            self.exit_script()

    def get_artist_from_filename( self, filename ):
        try:
            artist = filename
            song = filename
            basename = os.path.basename( filename )
            # Artist - Song.ext
            if ( self.settings[ "read_filename_format" ] == "0" ):
                artist = basename.split( "-", 1 )[ 0 ].strip()
                song = os.path.splitext( basename.split( "-", 1 )[ 1 ].strip() )[ 0 ]
            # Artist/Album/Song.ext or Artist/Album/Track Song.ext
            elif ( self.settings[ "read_filename_format" ] in ( "1", "2", ) ):
                artist = os.path.basename( os.path.split( os.path.split( filename )[ 0 ] )[ 0 ] )
                # Artist/Album/Song.ext
                if ( self.settings[ "read_filename_format" ] == "1" ):
                    song = os.path.splitext( basename )[ 0 ]
                # Artist/Album/Track Song.ext
                elif ( self.settings[ "read_filename_format" ] == "2" ):
                    song = os.path.splitext( basename )[ 0 ].split( " ", 1 )[ 1 ]
        except:
            # invalid format selected
            log( "failed to get artist and song from filename" )
        return artist, song

    def getMyPlayer( self ):
        self.MyPlayer = MyPlayer( xbmc.PLAYER_CORE_PAPLAYER, function=self.myPlayerChanged )
        self.myPlayerChanged( 2 )

    def myPlayerChanged( self, event ):
        log( "myPlayer event: %s" % ([ "stopped","ended","started" ][ event ]) )
        if ( event < 2 ):
            self.exit_script()
        else:
            for cnt in range( 5 ):
                songfile = ''
                try:
                    song = xbmc.Player().getMusicInfoTag().getTitle()
                    artist = xbmc.Player().getMusicInfoTag().getArtist()
                    log("Artist: %s - Song: %s" % (artist, song))
                    songfile = xbmc.getInfoLabel('Player.Filenameandpath')
                except:
                    pass
                if ( songfile and ( ( not song) or (not artist) or self.settings[ "read_filename" ] ) ):
                    artist, song = self.get_artist_from_filename( songfile )
                if ( songfile and ( self.songfile != songfile  ) ):
                    self.songfile = songfile
                    self.lock.acquire()
                    try:
                        self.timer.cancel()
                    except:
                        pass
                    self.lock.release()
                    self.find_lyrics( artist, song )
                    break
                xbmc.sleep( 50 )
            if (self.allowtimer and self.getControl( 110 ).size() > 1):
                self.lock.acquire()
                try:
                    self.timer.cancel()
                except:
                    pass
                self.lock.release()
                if self.lrc:
                    self.refresh()

class MyPlayer( xbmc.Player ):
    """ Player Class: calls function when song changes or playback ends """
    def __init__( self, *args, **kwargs ):
        xbmc.Player.__init__( self )
        self.function = kwargs[ "function" ]

    def onPlayBackStopped( self ):
        self.function( 0 )

    def onPlayBackEnded( self ):
        self.function( 1 )

    def onPlayBackStarted( self ):
        self.function( 2 )
