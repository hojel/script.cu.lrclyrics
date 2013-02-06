# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
"""
Scraper for http://lyrics.alsong.co.kr/

edge
"""

import socket
import hashlib
import urllib2
import xml.dom.minidom as xml
from utilities import *
from audiofile import AudioFile

__title__ = "Alsong"
__priority__ = '115'
__lrc__ = True

socket.setdefaulttimeout(10)

ALSONG_URL = "http://lyrics.alsong.net/alsongwebservice/service1.asmx"

ALSONG_TMPL = '''\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:SOAP-ENC="http://www.w3.org/2003/05/soap-encoding" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ns2="ALSongWebServer/Service1Soap" xmlns:ns1="ALSongWebServer" xmlns:ns3="ALSongWebServer/Service1Soap12">
<SOAP-ENV:Body>
<ns1:GetLyric5>
    <ns1:stQuery>
        <ns1:strChecksum>%s</ns1:strChecksum>
        <ns1:strVersion>2.2</ns1:strVersion>
        <ns1:strMACAddress />
        <ns1:strIPAddress />
    </ns1:stQuery>
</ns1:GetLyric5>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''

class alsongClient(object):
    '''
    privide alsong specific function, such as key from mp3
    '''
    @staticmethod
    def GetKeyFromFile(file):
        musf = AudioFile()
        musf.Open(file)
        ext = file[file.rfind('.'):].lower()
        if ext == '.ogg':
            buf = musf.ReadAudioStream(160*1024,11)	# 160KB excluding header
        elif ext == '.wma':
            buf = musf.ReadAudioStream(160*1024,24)	# 160KB excluding header
        else:
            buf = musf.ReadAudioStream(160*1024)	# 160KB from audio data
        musf.Close()
        # calculate hashkey
        m = hashlib.md5(); m.update(buf);
        return m.hexdigest()


class LyricsFetcher:
    def __init__( self ):
        self.base_url = "http://lyrics.alsong.co.kr/"

    def get_lyrics(self, song):
        log( "%s: searching lyrics for %s - %s" % (__title__, song.artist, song.title))
        lyrics = Lyrics()
        lyrics.song = song
        lyrics.source = __title__
        lyrics.lrc = __lrc__

        artist = song.artist
        title = song.title
        key = alsongClient.GetKeyFromFile( song.filepath )
        if not key:
            return None

        title = artist+' - '+title
        lyr = self.get_lyrics_from_list( (title,key,artist,song) )
        if not lyr:
            return None
        lyrics.lyrics = lyr
        return lyrics

    def get_lyrics_from_list(self, link):
        title,key,artist,song = link
        print key, artist, song

        headers = { 'Content-Type' : 'text/xml; charset=utf-8' }
        request = urllib2.Request(ALSONG_URL, ALSONG_TMPL % key, headers)
        try:
            response = urllib2.urlopen(request)
            Page = response.read()
        except Exception, e:
            print e

        tree = xml.parseString( Page )
        if tree.getElementsByTagName("strInfoID")[0].childNodes[0].data == '-1':
            return ''
        lyric = tree.getElementsByTagName("strLyric")[0].childNodes[0].data.replace('<br>','\n')
        return lyric.encode('utf-8')
