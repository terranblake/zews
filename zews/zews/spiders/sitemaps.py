import re
import logging
from pprint import pprint

from scrapy import signals
from scrapy.spiders import Spider
from scrapy.http import Request, XmlResponse
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots
from scrapy.utils.gz import gunzip, gzip_magic_number


logger = logging.getLogger(__name__)


class SitemapSpider(Spider):
    name = 'sitemaps'

    sitemap_limit = 10
    sitemap_urls = [
        'https://www.cnn.com/sitemaps/cnn/news.xml',
        'https://www.foxnews.com/sitemap.xml?type=news',
        # 'https://www.theverge.com/robots.txt',
        'https://www.nbcnews.com/sitemap/nbcnews/sitemap-news',
        'https://www.cnbc.com/sitemap_news.xml'
    ]
    sitemap_rules = [('', 'parse')]
    sitemap_follow = ['']
    sitemap_alternate_links = False
    sitemap_links_discovered = {}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._cbs = []
        for r, c in self.sitemap_rules:
            if isinstance(c, str):
                c = getattr(self, c)
            self._cbs.append((regex(r), c))
        self._follow = [regex(x) for x in self.sitemap_follow]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SitemapSpider, cls).from_crawler(crawler, *args, **kwargs)
        # crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        # crawler.signals.connect(spider.item_scraped, signal=signals.item_scraped)
        return spider

    def start_requests(self):
        for url in self.sitemap_urls:
            self.sitemap_links_discovered[url] = []
            yield Request(url, self._parse_sitemap)
        
    def sitemap_filter(self, entries):
        """This method can be used to filter sitemap entries by their
        attributes, for example, you can filter locs with lastmod greater
        than a given date (see docs).
        """
        for entry in entries:
            yield entry

    def _parse_sitemap(self, response):
        if response.url.endswith('/robots.txt'):
            for url in sitemap_urls_from_robots(response.text, base_url=response.url):
                yield Request(url, callback=self._parse_sitemap)
        else:
            body = self._get_sitemap_body(response)
            if body is None:
                logger.warning("Ignoring invalid sitemap: %(response)s",
                               {'response': response}, extra={'spider': self})
                return

            s = Sitemap(body)
            it = self.sitemap_filter(s)

            if s.type == 'sitemapindex':
                for loc in iterloc(it, self.sitemap_alternate_links):
                    if any(x.search(loc) for x in self._follow):
                        yield Request(loc, callback=self._parse_sitemap)
            elif s.type == 'urlset':
                for loc in iterloc(it, self.sitemap_alternate_links):
                    for r, c in self._cbs:
                        if r.search(loc):
                            yield Request(
                                loc, 
                                callback=c
                            )
                            break

    def _get_sitemap_body(self, response):
        """Return the sitemap body contained in the given response,
        or None if the response is not a sitemap.
        """
        if isinstance(response, XmlResponse):
            return response.body
        elif gzip_magic_number(response):
            return gunzip(response.body)
        # actual gzipped sitemap files are decompressed above ;
        # if we are here (response body is not gzipped)
        # and have a response for .xml.gz,
        # it usually means that it was already gunzipped
        # by HttpCompression middleware,
        # the HTTP response being sent with "Content-Encoding: gzip"
        # without actually being a .xml.gz file in the first place,
        # merely XML gzip-compressed on the fly,
        # in other word, here, we have plain XML
        elif response.url.endswith('.xml') or response.url.endswith('.xml.gz'):
            return response.body

    def parse(self, response, referrer=None):
        article_body = response.css('div.ArticleBody-articleBody .group').css('p::text').getall()
        yield {
            'body': article_body,
            'url': response.url
        }


def regex(x):
    if isinstance(x, str):
        return re.compile(x)
    return x


def iterloc(it, alt=False):
    for d in it:
        yield d['loc']

        # Also consider alternate URLs (xhtml:link rel="alternate")
        if alt and 'alternate' in d:
            yield from d['alternate']
