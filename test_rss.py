#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint
from datetime import datetime
from dateutil import parser, tz
import json
import feedparser
#import html2text # Non me gusta esta libreria porque mete markup en vez de puro texto
from pymongo import MongoClient


class Feed:
	def __init__(self,feed_info,db):
		self.info = feed_info
		self.db = db
		self.items = []
		feedparser.USER_AGENT = "MyApp/1.0 +http://example.com/"

	def parse_rss(self):
		feed = feedparser.parse(self.info["url"],self.info["etag"],self.info["modified"])
		if feed.status == 302:
			self.info["url"] = feed.href
			print("Url moved to: ",feed.href)
			self.store_feed_info()
			self.parse_rss()
			return
		if feed.status == 401:
			#feedgone, remove from db
			pass
		if feed.status ==304:
			# feed with nothing new
			print("Etag, last_modifier: ",feed.status)
			return ""

		self.info["etag"] = feed.etag
		self.info["last_modifier"] = feed.modified

		for entry in feed.entries:
			print(entry.title)
			item = {"title" : entry.title, "link" : entry.link, "published_at_str" : entry.published , "published_at_time" : entry.published_parsed, "saved_at" : datetime.now(), "author" : entry.author}
			try:
				item["content_html"] = entry.description
			except:
				print("Error in content")

			#item["content_text"] = html2text.html2text(item["content_html"])
			self.items.append(item)

	def update_feed_info(self):
		aux = db.replace_one(COLLECTION_NAME_SOURCES,self.info["name"],self.info)
		print(aux.matched_count)

	def store(self):
		if len(self.items):
			# Store all new items
			transaction_ids = self.db.store_many(self.info["name"],self.items)
			# Store ETAG, LAST-MODIFIED and time.now in Sources Collection
			self.update_feed_info()

	def print_titles(self):
		for item in self.items:
			print(item["title"])


class DatabaseMongo:
	def __init__(self,host,port):
		client = MongoClient(host, port)
		self.db = client[DB_NAME]

	def store(self,collection,row):
		return self.db[collection].insert(row)

	def store_many(self,collection,rows):
		return self.db[collection].insert_many(rows)

	def read_all(self,collection):
		return self.db[collection].find()

	def replace_one(self,collection,name,row):
		return self.db[collection].replace_one({"name":name},row)




###### MAIN ######
DB_NAME = "feeds"
COLLECTION_NAME_SOURCES = "sources"

pp = pprint.PrettyPrinter(indent=4)


db = DatabaseMongo('localhost', 27017)

for source in db.read_all(COLLECTION_NAME_SOURCES):
	feed = Feed(source,db)
	feed.parse_rss()
	feed.print_titles()
	feed.store()

	#print(feed.items[1]["content_text"])
