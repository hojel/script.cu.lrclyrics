# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
"""
Scraper for http://newlyrics.gomtv.com/

edge
"""

import socket
import hashlib
import urllib
import re
from utilities import *
from audiofile import AudioFile

__title__ = "GomAudio"
__priority__ = '135'
__lrc__ = True

socket.setdefaulttimeout(10)

GOM_URL = "http://newlyrics.gomtv.com/cgi-bin/lyrics.cgi?cmd=find_get_lyrics&file_key=%s&title=%s&artist=%s&from=gomaudio_local"

class gomClient(object):
    '''
    privide Gom specific function, such as key from mp3
    '''
    @staticmethod
    def GetKeyFromFile(file):
        musf = AudioFile()
        musf.Open(file)
        buf = musf.ReadAudioStream(100*1024)	# 100KB from audio data
        musf.Close()
        # calculate hashkey
        m = hashlib.md5(); m.update(buf);
        return m.hexdigest()

    @staticmethod
    def mSecConv(msec):
        s,ms = divmod(msec/10,100)
        m,s = divmod(s,60)
        return m,s,ms

class LyricsFetcher:
    def __init__( self ):
        self.base_url = "http://newlyrics.gomtv.com/"

    def get_lyrics(self, artist, song, songfile):
        log( "%s: searching lyrics for %s - %s" % (__title__, song.artist, song.title))
        lyrics = Lyrics()
        lyrics.song = song
        lyrics.source = __title__
        lyrics.lrc = __lrc__

        artist = song.artist
        title = song.title
        key = gomClient.GetKeyFromFile( song.filepath )
        if not key:
            return None

        title = artist+' - '+song
        lyr = self.get_lyrics_from_list( (title,key,artist,song) )
        if not lyr:
            return None
        lyrics.lyrics = lyr
        return lyrics

    def get_lyrics_from_list(self, link):
        title,key,artist,song = link
        print key, artist, song
        print GOM_URL %(key, urllib.quote(song.decode("utf-8").encode("euc-kr")), urllib.quote(artist.decode("utf-8").encode("euc-kr")) )

        try:
            response = urllib.urlopen( GOM_URL %(key, urllib.quote(song.decode("utf-8").encode("euc-kr")), urllib.quote(artist.decode("utf-8").encode("euc-kr")) ) )
            Page = response.read()
        except Exception, e:
            print e

        if Page[:Page.find('>')+1] != '<lyrics_reply result="0">':
            print Page[:Page.find('>')+1]
            return ''
        syncs = re.compile('<sync start="(\d+)">([^<]*)</sync>').findall(Page)
        lyric = []
        lyric.append( "[ti:%s]" %song )
        lyric.append( "[ar:%s]" %artist )
        for sync in syncs:
            # timeformat conversion
            t = "%02d:%02d.%02d" % gomClient.mSecConv( int(sync[0]) )
            # unescape string
            s = unicode(sync[1], "euc-kr").encode("utf-8").replace("&apos;","'").replace("&quot;",'"')
            lyric.append( "[%s]%s" %(t,s) )
        return '\n'.join( lyric )
