#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint
from datetime import datetime
from dateutil import parser, tz
import json
import feedparser
from pymongo import MongoClient
from time import mktime


def struct_time_to_timestamp(struct_time):
	return mktime(struct_time)


class Feed:
	def __init__(self,feed_info,db):
		self.info = feed_info
		self.db = db
		self.items = []
		#feedparser.USER_AGENT = "MyApp/1.0 +http://example.com/"
		if not "etag" in self.info.keys():
			self.info["etag"] = ""
		if not "modified" == self.info.keys():
			self.info["modified"] = ""
		if not "last_time_item" in self.info.keys():
			self.info["last_time_item"] = 0

	def run(self):
		self.print_feed_name()
		self.fetch_rss()
		self.parse_rss()
		self.store()
		self.print_titles()
		self.update_feed_info()


	def fetch_rss(self):
		try:
			self.feed = feedparser.parse(self.info["url"],self.info["etag"],self.info["modified"])
			status = self.feed.status
		except:
			print(" Error in feedparser: ",self.feed)
			return -1

		if status == 302:
			self.info["url"] = self.feed.href
			print(" Url moved to: ",self.feed.href,". Restart run feed")
			self.update_feed_info()
			self.run()
			return 0
		if status == 401:
			#feedgone, remove from db
			pass
		if status == 304:
			# feed with nothing new
			print(" Nothing new in ",self.info["name"],", etag status: ",self.feed.status)
			return 0
		try:
			self.info["etag"] = self.feed.etag
			self.info["modified"] = self.feed.modified
		except:
			pass

		return 1

	def parse_rss(self):
		new_last_time_item = 0
		for entry in self.feed.entries:
			#print(entry.title)
			item = {}
			try:
				item["published_at_time"] = struct_time_to_timestamp(entry.published_parsed)
				#print(item["published_at_time"])
			except:
				print("Error in published_parsed")

			# If item is not new, skip
			if self.info["last_time_item"] >= item["published_at_time"]:
				print("  Item already in db")
				continue
			else:
				if new_last_time_item <  item["published_at_time"]:
					new_last_time_item =  item["published_at_time"]

			try:
				item.update({"title" : entry.title, "link" : entry.link , "saved_at" : datetime.now(), "author" : entry.author})
			except:
				print("  Error in title, or link, or author")

			try:
				item["published_at_str"]  = entry.published
			except:
				print("  Error in published")
			try:
				item["content_html"] = entry.description
			except:
				print("  Error in content")

			#item["content_text"] = html2text.html2text(item["content_html"])
			self.items.append(item)

		# Update last item time in feed info
		if new_last_time_item != 0:
			self.info["last_time_item"] = new_last_time_item

		return len(self.items)

	def update_feed_info(self):
		aux = db.replace_one(COLLECTION_NAME_SOURCES,self.info["name"],self.info)
		#print(aux.matched_count)

	def store(self):
		if len(self.items) != 0:
			# Store all new items
			transaction_ids = self.db.store_many(self.info["name"],self.items)
			# Store ETAG, LAST-MODIFIED and time.now in Sources Collection

	def print_titles(self):
		for item in self.items:
			try:
				print(" - ",item["title"])
			except:
				print(" Error printing titles, full row: ",item)

	def print_feed_name(self):
		print(self.info["name"])


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
#pp = pprint.PrettyPrinter(indent=4)
DB_NAME = "feeds"
COLLECTION_NAME_SOURCES = "0_sources"
db = DatabaseMongo('localhost', 27017)


if __name__ == '__main__':
	for source in db.read_all(COLLECTION_NAME_SOURCES):
		Feed(source,db).run()
