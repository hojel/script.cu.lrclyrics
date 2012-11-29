#-*- coding: UTF-8 -*-
"""
Scraper for http://www.baidu.com

taxigps
"""

import urllib
import socket
import re
import chardet
import difflib
from utilities import *

__title__ = "Baidu"
__priority__ = '120'
__lrc__ = True

socket.setdefaulttimeout(10)

class LyricsFetcher:
    def __init__( self ):
        self.BASE_URL = 'http://box.zhangmen.baidu.com/x?op=12&count=1&title=%s$$%s$$$$'
        self.LRC_URL = 'http://box.zhangmen.baidu.com/bdlrc/%d/%d.lrc'

    def get_lyrics(self, artist, song):
        log( "%s: searching lyrics for %s - %s" % (__title__, artist, song))
        try:
            url = self.BASE_URL % (song, artist)
            xml_str = urllib.urlopen(url).read()
            lrcid_pattern = re.compile(r'<lrcid>(.+?)</lrcid>')
            lrcid = int(re.search(lrcid_pattern, xml_str).group(1))
            lrc_url = self.LRC_URL % (lrcid/100, lrcid)
            lyrics = urllib.urlopen(lrc_url).read()
        except:
            log( "%s: %s::%s (%d) [%s]" % (
                   __title__, self.__class__.__name__,
                   sys.exc_info()[ 2 ].tb_frame.f_code.co_name,
                   sys.exc_info()[ 2 ].tb_lineno,
                   sys.exc_info()[ 1 ]
                   ))
            return None

        enc = chardet.detect(lyrics)
        if (enc['encoding'] == 'utf-8'):
            return lyrics
        else:
            return unicode( lyrics, enc['encoding'], 'ignore' ).encode( "utf-8")
