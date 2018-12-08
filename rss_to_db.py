#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Common libs
import pprint
import json
import time
from datetime import datetime
from dateutil import parser, tz
import sys
import os
# Feed lib
import feedparser
# Pymongo lib
from pymongo import MongoClient
# Threading
from concurrent import futures
import threading
# Parse command line arguments
import argparse
# Chain map allow the code to make assigns in cascade Argument, ENV, default
from collections import ChainMap

def struct_time_to_timestamp(struct_time):
	return time.mktime(struct_time)


class Feed:
	def __init__(self,feed_info,db):
		self.info = feed_info
		self.info["name"] = self.info["name"].strip()
		self.db = db
		self.items = []
		self.errors = []
		#feedparser.USER_AGENT = "MyApp/1.0 +http://example.com/"
		if not "etag" in self.info.keys():
			self.info["etag"] = ""
		if not "modified" == self.info.keys():
			self.info["modified"] = ""
		if not "last_time_item" in self.info.keys():
			self.info["last_time_item"] = 0

	def run(self):
		#.print_feed_name()
		fetch_code = self.fetch_rss()
		if fetch_code <0:
			return -1
		number_of_items = self.parse_rss()
		if number_of_items > 0:
			self.store()
			#.print_titles()
		self.update_feed_info()
		print(self.create_log_info())
		if len(self.errors)>0:
			print(self.create_log_error())
		return number_of_items

	def fetch_rss(self):
		try:
			self.feed = feedparser.parse(self.info["url"],self.info["etag"],self.info["modified"])
			status = self.feed.status
		except:
			self.errors.append(" Feedparser:"+str(self.feed))
			return -1
		if self.feed.bozo == 1:
			# XML not well-formed, consider to delete from Sources
			self.errors.append(" Bozo")
			return -1

		if status == 200:
			try:
				self.info["etag"] = self.feed.etag
				self.info["modified"] = self.feed.modified
			except:
				pass

		elif status == 302 or status == 301:
			self.info["url"] = self.feed.href
			self.errors.append(" Url moved to:"+self.feed.href+". Restart run feed")
			self.update_feed_info()
			self.fetch_rss()
			return 0
		elif status == 304:
			# feed with nothing new
			#print(" Nothing new in ",self.info["name"],", etag status: ",self.feed.status)
			return 0
		elif status == 401:
			# feedgone, remove from db
			self.errors.append(" Url gone (401)")
			pass
			return -1
		elif status == 404:
			# error accessing url, check several times and remove if it's persists
			return -1
		else:
			self.errors.append( "HTTP Error not handled: "+str(status))
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
					#print("  Item already in db")
					continue
				else:
					if new_last_time_item <  item["published_at_time"]:
						new_last_time_item =  item["published_at_time"]
			except:
				self.errors.append(" Error in published_parsed!")

			try:
				item.update({"title" : entry.title, "link" : entry.link , "saved_at" : datetime.now()})
			except:
				self.errors.append(" Error in title or link")
			try:
				item["author"] = entry.author
			except:
				item["author"] = ""
				self.errors.append(" Error in author")
			try:
				item["published_at_str"]  = entry.published
			except:
				self.errors.append(" Error in published")
			try:
				item["content_html"] = entry.description
			except:
				self.errors.append(" Error in content")

			#item["content_text"] = html2text.html2text(item["content_html"])
			self.items.append(item)

		# Update last item time in feed info
		if new_last_time_item != 0:
			self.info["last_time_item"] = new_last_time_item

		return len(self.items)

	def update_feed_info(self):
		aux = db.replace_one(ENV["DB_COLLECTION_SOURCES"],self.info["name"],self.info)
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

	def create_log_info(self):
		line = str(datetime.now()) + " - INFO: " + self.info["name"] + " - " + str(len(self.items)) + " new feeds. "
		return line

	def create_log_error(self):
		line = str(datetime.now()) + " - ERROR: " + self.info["name"] + " - Errors: " + ", ".join(self.errors)
		return line


class DatabaseMongo:
	def __init__(self,host,port):
		client = MongoClient(host, port)
		self.db = client[ENV["DB_NAME"]]

	def store(self,collection,row):
		return self.db[collection].insert(row)

	def store_many(self,collection,rows):
		return self.db[collection].insert_many(rows)

	def read_all(self,collection):
		return self.db[collection].find()

	def replace_one(self,collection,name,row):
		return self.db[collection].replace_one({"name":name},row)


###### MAIN ######
if __name__ == '__main__':
	# DEFAULT ENV
	default_env = {"DB_NAME":"feeds","DB_COLLECTION_SOURCES":"0_sources","DB_HOST":"localhost","DB_PORT": "27017","EXECUTION":"Threaded"}

	# Command line argument parser
	parser = argparse.ArgumentParser(prog="rss_to_db",description='Check rss urls for new content and store it',epilog="Execution or rss_to_db finished!")
	#parser.add_argument("-s",'--sequential', action='store_true',help="Execute the program scuentially, instead of the default threaded execution")
	for key in default_env:
		parser.add_argument("--"+key)
	args = parser.parse_args()
	command_line_arguments = {key:value for key, value in vars(args).items() if value}


	os_env = {key:value for key, value in os.environ.items() if (key in default_env)}
	print(os_env)

	ENV = ChainMap(command_line_arguments, os_env, default_env) # Especial dict in with when access to a key, use the key with more priority if it exists

	print(ENV)

	# DB Initialization
	db = DatabaseMongo(ENV["DB_HOST"],  int(ENV["DB_PORT"]))

	# Execution
	if ENV["EXECUTION"] == "sequential":
		print("# Sequence execution")
		for source in db.read_all(ENV["DB_COLLECTION_SOURCES"]):
			Feed(source,db).run()
	else:
		print("# Threaded execution")
		def exec_feed(source):
			Feed(source,db).run()
		ex = futures.ThreadPoolExecutor(max_workers=32) # My processor has 4 cores with 8 virtual cores each, so 32 threads in theory
		results = ex.map(exec_feed, db.read_all(ENV["DB_COLLECTION_SOURCES"]))
		print("# Finished threaded execution")
