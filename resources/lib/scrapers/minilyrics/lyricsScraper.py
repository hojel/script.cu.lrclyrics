#-*- coding: UTF-8 -*-
"""
Scraper for http://www.viewlyrics.com

taxigps
"""

import urllib
import urllib2
import socket
import re
import difflib
from hashlib import md5
import chardet
from utilities import *

__title__ = "MiniLyrics"
__priority__ = '110'
__lrc__ = True

socket.setdefaulttimeout(10)

class LyricsFetcher:
    def __init__( self ):
        self.proxy = None

    def htmlEncode(self,string):
        chars = {'\'':'&apos;','"':'&quot;','>':'&gt;','<':'&lt;','&':'&amp;'}
        for i in chars:
            string = string.replace(i,chars[i])
        return string

    def htmlDecode(self,string):
        entities = {'&apos;':'\'','&quot;':'"','&gt;':'>','&lt;':'<','&amp;':'&'}
        for i in entities:
            string = string.replace(i,entities[i])
        return string

    def decryptResultXML(self,value):
        magickey = ord(value[1])
        neomagic = ''
        for i in range(20, len(value)):
            neomagic += chr(ord(value[i]) ^ magickey)
        return neomagic

    def miniLyricsParser(self,response):
        text = self.decryptResultXML(response)
        lines = text.splitlines()
        ret = []
        for line in lines:
            if line.strip().startswith("<fileinfo filetype=\"lyrics\" "):
                loc = []
                loc.append(self.htmlDecode(re.search('link=\"([^\"]*)\"',line).group(1)))
                if not loc[0].lower().endswith(".lrc"):
                    continue
                if(re.search('artist=\"([^\"]*)\"',line)):
                    loc.insert(0,self.htmlDecode(re.search('artist=\"([^\"]*)\"',line).group(1)))
                else:
                    loc.insert(0,' ')
                if(re.search('title=\"([^\"]*)\"',line)):
                    loc.insert(1,self.htmlDecode(re.search('title=\"([^\"]*)\"',line).group(1)))
                else:
                    loc.insert(1,' ')
                ret.append(loc)
        return ret

    def get_lyrics(self, artist, song):
        log( "%s: searching lyrics for %s - %s" % (__title__, artist, song))
        xml ="<?xml version=\"1.0\" encoding='utf-8'?>\r\n"
        xml+="<search filetype=\"lyrics\" artist=\"%s\" title=\"%s\" " % (artist, song)
        xml+="ClientCharEncoding=\"utf-8\"/>\r\n"
        md5hash = md5(xml+"Mlv1clt4.0").digest()
        request = "\x02\x00\x04\x00\x00\x00%s%s" % (md5hash, xml)
        del md5hash,xml
        url = "http://www.viewlyrics.com:1212/searchlyrics.htm"
        #url = "http://search.crintsoft.com/searchlyrics.htm"
        req = urllib2.Request(url,request)
        req.add_header("User-Agent", "MiniLyrics")
        if self.proxy:
            opener = urllib2.build_opener(urllib2.ProxyHandler(self.proxy))
        else:
            opener = urllib2.build_opener()
        try:
            response = opener.open(req).read()
        except:
            log( "%s: %s::%s (%d) [%s]" % (
                   __title__, self.__class__.__name__,
                   sys.exc_info()[ 2 ].tb_frame.f_code.co_name,
                   sys.exc_info()[ 2 ].tb_lineno,
                   sys.exc_info()[ 1 ]
                   ))
            return None

        lrcList = self.miniLyricsParser(response)
        for x in lrcList:
            # use fuzzy match to find an 'exact' match in the results
            if (difflib.SequenceMatcher(None, artist.lower(), x[0].lower()).ratio() > 0.8) and (difflib.SequenceMatcher(None, song.lower(), x[1].lower()).ratio() > 0.8):
                try:
                    f = urllib.urlopen(x[2])
                    lyrics = f.read()
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
                    return unicode( lyrics, enc['encoding'] ).encode( "utf-8")
        return None
