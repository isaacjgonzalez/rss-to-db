import pprint
from datetime import datetime
from dateutil import parser, tz
import json
import feedparser
import html2text # Non me gusta esta libreria porque mete markup en vez de puro texto
from pymongo import MongoClient


class Feed:
	def __init__(self,name,url,db):
		self.name = name
		self.url = url
		self.items = []
		self.db = db
		
	def parse_rss(self):
		feed = feedparser.parse(self.url)
		#feed_title = feed['feed']['title']
		for entry in feed.entries:
			item = {"title" : entry.title, "link" : entry.link, "published_at_str" : entry.published , "published_at_time" : entry.published_parsed.astimezone(tz.tzutc()), "saved_at" : datetime.now(), "author" : entry.author, "content_html" : entry.content[0]["value"] }
			
			item["content_text"] = html2text.html2text(item["content_html"])
			self.items.append(item)
			
	def store(self):
		transaction_id = self.db.store(self.name,self.items[0])




class DatabaseMongo:
	def __init__(self,host,port):
		client = MongoClient(host, port)
		self.db = client['feeds']
	
	def store(self,collection,row):
		self.db[collection].insert(row)
		
	
		    

###### MAIN ######

pp = pprint.PrettyPrinter(indent=4)


db = DatabaseMongo('localhost', 27017)
feed = Feed("pythoninsider","http://feeds.feedburner.com/PythonInsider",db)
feed.parse_rss()
feed.store()

#print(feed.items[1]["content_text"])
 


