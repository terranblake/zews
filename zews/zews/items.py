# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SitemapItem(scrapy.Item):
    # the url of the article
    url = scrapy.Field()
    # the source sitemap where the article was pulled from
    referrer = scrapy.Field()