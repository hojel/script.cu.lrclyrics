#-*- coding: UTF-8 -*-
import sys, re, urllib2, socket, HTMLParser
import xbmc, xbmcaddon
if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson
from utilities import *

__title__ = 'lyricwiki'

socket.setdefaulttimeout(10)

class LyricsFetcher:
    def __init__( self ):
        self.url = 'http://lyrics.wikia.com/api.php?artist=%s&song=%s&fmt=realjson'

    def get_lyrics(self, artist, song):
        log( "%s: searching lyrics for %s - %s" % (__title__, artist, song))
        req = urllib2.urlopen(self.url % (urllib2.quote(artist), urllib2.quote(song)))
        response = req.read()
        req.close()
        data = simplejson.loads(response)
        try:
            self.page = data['url']
        except:
            return ''
        if not self.page.endswith('action=edit'):
            log( "%s: search url: %s" % (__title__, self.page))
            req = urllib2.urlopen(self.page)
            response = req.read()
            req.close()
            matchcode = re.search('lyricbox.*?div>(.*?)<!--', response)
            try:
                lyricscode = (matchcode.group(1))
                htmlparser = HTMLParser.HTMLParser()
                lyricstext = htmlparser.unescape(lyricscode).replace('<br />', '\n')
                lyrics = re.sub('<[^<]+?>', '', lyricstext)
                return lyrics, False
            except:
                return '', False
        else:
            return '', False
