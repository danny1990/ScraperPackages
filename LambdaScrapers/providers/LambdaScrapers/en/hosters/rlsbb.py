# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 12-03-2018 by JewBMX in Scrubs.

import re,urllib,urlparse,json
from providerModules.LambdaScrapers import cleantitle,client,control,debrid,log_utils,source_utils,cfscrape


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['rlsbb.ru','rlsbb.to','rlsbb.com']
        self.base_link = 'http://rlsbb.ru'
        self.search_base_link = 'http://search.rlsbb.ru'
        self.search_cookie = 'serach_mode=rlsbb'
        self.search_link = '/lib/search526049.php?phrase=%s&pindex=1&content=true'
        self.scraper = cfscrape.create_scraper()


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'title': title, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
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
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            if url == None: return sources
            
            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
            hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
            query = '%s %s-S%02dE%02d' % (
                data['tvshowtitle'], data['year'], int(data['season']), int(data['episode'])) \
                if 'tvshowtitle' in data else '%s %s' % (data['title'], data['year'])
            query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)
            query = query.replace("&", "and")
            query = query.replace("  ", " ")
            query = query.replace(" ", "-")
            url = self.search_link % urllib.quote_plus(query).lower()
            url = urlparse.urljoin(self.base_link, url)
            url = "http://rlsbb.ru/" + query
            if 'tvshowtitle' not in data: url = url + "-1080p"
            r = self.scraper.get(url).content
            if r == None and 'tvshowtitle' in data:
                season = re.search('S(.*?)E', hdlr)
                season = season.group(1)
                query = title
                query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)
                query = query + "+S" + season
                query = query.replace("&", "and")
                query = query.replace("  ", " ")
                query = query.replace(" ", "+")
                url = "http://rlsbb.ru/" + query.lower()
                r = self.scraper.get(url).content
            posts = client.parseDOM(r, "div", attrs={"class": "content"})
            hostDict = hostprDict + hostDict
            items = []
            for post in posts:
                try:
                    u = client.parseDOM(post, 'a', ret='href')
                    for i in u:
                        try:
                            name = str(i)
                            if hdlr in name.upper(): items.append(name)
                        except:
                            pass
                except:
                    pass
            seen_urls = set()
            for item in items:
                try:
                    info = []
                    url = str(item)
                    url = client.replaceHTMLCodes(url)
                    url = url.encode('utf-8')
                    if url in seen_urls: continue
                    seen_urls.add(url)
                    host = url.replace("\\", "")
                    host2 = host.strip('"')
                    host = re.findall('([\w]+[.][\w]+)$', urlparse.urlparse(host2.strip().lower()).netloc)[0]
                    if not host in hostDict: raise Exception()
                    if any(x in host2 for x in ['.rar', '.zip', '.iso']): continue
                    if '720p' in host2:
                        quality = 'HD'
                    elif '1080p' in host2:
                        quality = '1080p'
                    else:
                        quality = 'SD'
                    info = ' | '.join(info)
                    host = client.replaceHTMLCodes(host)
                    host = host.encode('utf-8')
                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': host2, 'info': info, 'direct': False, 'debridonly': True})
                except:
                    pass
            check = [i for i in sources if not i['quality'] == 'CAM']
            if check: sources = check
            return sources
        except:
            return sources


    def resolve(self, url):
        return url

