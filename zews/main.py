# Run scrapy in-process instead of using the scrapy crawl command.
# This makes it easier to demonstrate on repl.it, but in the real 
# world you'd probably use "scrapy crawl" instead.
from scrapy.crawler import CrawlerProcess
from zews.spiders import sitemaps
process = CrawlerProcess()
process.crawl(sitemaps.SitemapSpider)
process.start()