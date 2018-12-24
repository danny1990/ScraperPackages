# -*- coding: UTF-8 -*-
#######################################################################
 # ----------------------------------------------------------------------------
 # "THE BEER-WARE LICENSE" (Revision 42):
 # @tantrumdev wrote this file.  As long as you retain this notice you
 # can do whatever you want with this stuff. If we meet some day, and you think
 # this stuff is worth it, you can buy me a beer in return. - Muad'Dib
 # ----------------------------------------------------------------------------
#######################################################################
# -Cleaned and Checked on 10-10-2018 by JewBMX in Yoda.

import re,traceback,urllib,urlparse

from providerModules.LambdaScrapers import cleantitle
from providerModules.LambdaScrapers import client
from providerModules.LambdaScrapers import debrid
from providerModules.LambdaScrapers import source_utils
from providerModules.LambdaScrapers import log_utils

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['2ddl.ws'] 
        self.base_link = 'http://2ddl.ws/?s='
        #self.search_link = '/search/%s/feed/rss2/'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'title': title, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            failure = traceback.format_exc()
            log_utils.log('2DDL - Exception: \n' + str(failure))
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            failure = traceback.format_exc()
            log_utils.log('2DDL - Exception: \n' + str(failure))
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url == None: return

            url = urlparse.parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
            url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
            url = urllib.urlencode(url)
            return url
        except:
            failure = traceback.format_exc()
            log_utils.log('2DDL - Exception: \n' + str(failure))
            return

    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            query_bases = []
            options = []
            html = ""

            log_utils.log("2DDL debug")

            if url == None: return sources

            

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
            hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']

            # TVshows
            if 'tvshowtitle' in data:
                
                query_bases.append('%s ' % (data['tvshowtitle']))  # (ex 9-1-1 become 911)
                # tvshowtitle + year (ex Titans-2018-s01e1 or Insomnia-2018-S01)
                query_bases.append('%s %s ' % (data['tvshowtitle'], data['year']))

                options.append('S%02d E%02d' % (int(data['season']), int(data['episode'])))
                # season only (ex ozark-S02, group of episodes)
                options.append('S%02d' % (int(data['season'])))
                
                html = self.search(query_bases, options)

            else:
                #log_utils.log("2DDL Movie")
                #  Movie
                query_bases.append('%s ' % (data['title']))
                options.append('%s' % (data['year']))
                html = self.search(query_bases, options)

            urls  = client.parseDOM(html, 'a', ret="href", attrs={"class":"more-link"})
            #log_utils.log("2DDL urls : " + str(urls))

            r = ""

            for url in urls:

                html = client.request(url)

                while html != "":
                    try:
                        r += (html.split  ("<singlelink>"))[1].split("<Download>")[0]
                        html    =  html.split("<Download>")[1]
                    except:
                        html = ""
            
            posts = client.parseDOM(r, 'a', ret='href') 

            log_utils.log("2DDL posts = "+ str(posts))

            hostDict = hostprDict + hostDict

            items = []

            for post in posts:
                try:
                    item = str(post)
                    # have to filter on title and space become . in url name
                    # exemple "this is us" return everything with "us" , with filter return this.is.us
                    if data['episode'] in item.upper() and data['season'] in item.upper() and title.upper().replace(" ",".") in item.upper(): 
                        items.append(item)
                except:
                    pass

            log_utils.log("2DDL items : " + str(items))

            for item in items:
                try:

                    info = []
                    url = str(item)
                    url = client.replaceHTMLCodes(url)
                    url = url.encode('utf-8')

                    host = url.replace("\\", "")
                    host2 = host.strip('"')
                    host = re.findall('([\w]+[.][\w]+)$', urlparse.urlparse(host2.strip().lower()).netloc)[0]

                    if not host in hostDict: raise Exception()
                    host = client.replaceHTMLCodes(host)
                    host = host.encode('utf-8')
                    
                    if any(x in host2 for x in ['.rar', '.zip', '.iso']): continue

                    if '720p' in host2:
                        quality = 'HD'
                    elif '1080p' in host2:
                        quality = '1080p'
                    else:
                        quality = 'SD'

                    info = ' | '.join(info)

                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'info': info,
                                    'direct': False, 'debridonly': True})
                except:
                    pass

            check = [i for i in sources if not i['quality'] == 'CAM']
            if check: sources = check
            #log_utils.log("2DDL sources = " + str(sources))
        except:
            failure = traceback.format_exc()
            log_utils.log('2DDL - Exception: \n' + str(failure))

        return sources    # one return is enough !

    def search(self, query_bases, options):
        i = 0
        result = None
        for query_base in query_bases:

            q = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query_base)
            q = q.replace("  ", " ").replace(" ", "+")
            
            for option in options:
                query = q + option
                log_utils.log("2DDL query : " + query)
            
                #result = self.scraper.get("http://search.rlsbb.ru/" + q).content        
                result = client.request(self.base_link + q)

                if (result != None):
                    log_utils.log("2DDL test " + str(i) + " Ok :" + str(len(result)))
                    return result
                else:
                    log_utils.log("2DDL test " + str(i) + " = None - trying test " + str(i+1))
                    i += 1
                    
        return None

    def resolve(self, url):
        return url
