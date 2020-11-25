# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from .items import SitemapItem
import uuid
import csv

class SitemapPipeline:
    def process_item(self, item, spider):
        return item

class TrainingPipeline:
    def process_item(self, item, spider):
        article_text = item['paragraphs']
        url = item['url']
        # symbols = item['symbols']
        print(article_text)
        print(" ")
        sent_dict = ({'url':url, 'text': article_text})
        with open('/Users/danielkearney-spaw/Desktop/vader_training/cnbc_trial_text.csv', 'a') as file:
            fieldnames = ['url', 'text']
            writer = csv.DictWriter(file,fieldnames=fieldnames)
            writer.writerow(sent_dict)


