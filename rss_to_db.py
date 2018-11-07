#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Common libs
import pprint
import json
import time
from datetime import datetime
from dateutil import parser, tz
import sys
# Feed lib
import feedparser
# Pymongo lib
from pymongo import MongoClient
# Threading
from concurrent import futures
import threading


def struct_time_to_timestamp(struct_time):
	return time.mktime(struct_time)


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
		fetch_code = self.fetch_rss()
		if fetch_code <0:
			return -1
		number_of_items = self.parse_rss()
		if number_of_items > 0:
			self.store()
			self.print_titles()
		self.update_feed_info()
		return number_of_items

	def fetch_rss(self):
		try:
			self.feed = feedparser.parse(self.info["url"],self.info["etag"],self.info["modified"])
			status = self.feed.status
		except:
			print(" Error in feedparser: ",self.feed)
			return -1

		if status == 200:
			try:
				self.info["etag"] = self.feed.etag
				self.info["modified"] = self.feed.modified
			except:
				pass

		elif status == 302 or status == 301:
			self.info["url"] = self.feed.href
			print(" Url moved to: ",self.feed.href,". Restart run feed")
			self.update_feed_info()
			self.fetch_rss()
			return 0
		elif status == 304:
			# feed with nothing new
			print(" Nothing new in ",self.info["name"],", etag status: ",self.feed.status)
			return 0
		elif status == 401:
			# feedgone, remove from db
			pass
			return -1
		elif status == 404:
			# error accessing url, check several times and remove if it's persists
			return -1
		else:
			print( "HTTP Error not handled: ",status)
			return -1

		return 1

	def parse_rss(self):
		new_last_time_item = 0
		for entry in self.feed.entries:
			#print(entry.title)
			item = {}
			try:
				item["published_at_time"] = struct_time_to_timestamp(entry.published_parsed)
				# If item is not new, skip
				if self.info["last_time_item"] >= item["published_at_time"]:
					print("  Item already in db")
					continue
				else:
					if new_last_time_item <  item["published_at_time"]:
						new_last_time_item =  item["published_at_time"]
			except:
				print("  Error in published_parsed! Check if content is not new can't be done!")

			try:
				item.update({"title" : entry.title, "link" : entry.link , "saved_at" : datetime.now()})
			except:
				print("  Error in title, or link, or author")
			try:
				item["author"] = entry.author
			except:
				print("  Error in author")
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
		print("\n",self.info["name"])


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
	print("# Add -p to execute the threads. Start:")
	if len(sys.argv) > 1 and sys.argv[1] == "-p":
		print("# Threaded execution")
		def exec_feed(source):
			Feed(source,db).run()
		ex = futures.ThreadPoolExecutor(max_workers=32) # My processor has 4 cores with 8 virtual cores each, so 32 threads in theory
		results = ex.map(exec_feed, db.read_all(COLLECTION_NAME_SOURCES))
		print("# Finished threaded execution")
	else:
		print("# Sequence execution")
		for source in db.read_all(COLLECTION_NAME_SOURCES):
			Feed(source,db).run()

	print("# Finsh rss_to_db")
