#!/usr/bin/python3
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
# Wget to download enclosures
import wget
# Newspaper3K is a library to download full text content and other
from newspaper import Article
# Opengraph lib to extract top_image
import opengraph


from image_cache import image_download_create_thumbnails
import post_to_wp


def struct_time_to_timestamp(struct_time):
	return time.mktime(struct_time)


class Feed:
	def __init__(self,feed_info,db):
		self.info = feed_info
		self.info["name"] = self.info["name"].strip()
		self.db = db
		self.items = []
		self.errors = []
		if "collection" in feed_info:
			self.info["collection"] = feed_info["collection"]
		else:
			self.info["collection"] = feed_info["name"]
		#feedparser.USER_AGENT = "MyApp/1.0 +http://example.com/"
		if not "etag" in self.info.keys():
			self.info["etag"] = ""
		if not "modified" == self.info.keys():
			self.info["modified"] = ""
		if not "last_time_item" in self.info.keys():
			self.info["last_time_item"] = 0

	def run(self):
		#self.print_feed_name()
		fetch_code = self.fetch_rss()
		if fetch_code <0:
			return -1
		number_of_items = self.parse_rss()
		self.enhance_newspaper()
		self.enhance_opengraph()
		if ENV["IMAGE_CACHE"] == "ON":
			self.image_cache()
		if number_of_items > 0:
			self.store()
		if ENV["DOWNLOAD"] == "ON":
			self.enclosures()
		if ENV["POST_TO_WP"] == "ON":
			self.post_to_wp()
		self.update_feed_info()
		print(self.create_log_info())
		if len(self.errors)>0:
			print(self.create_log_error())
		return number_of_items

	def fetch_rss(self):
		try:
			self.feed = feedparser.parse(self.info["url"],self.info["etag"],self.info["modified"])
			status = self.feed.status
		except Exception as e:
			self.errors.append(" Feedparser "+str(self.feed)+" e: "+str(e))
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
			except Exception as e:
				self.errors.append(" Error in published_parsed! " + str(e))

			try:
				item.update({"title" : entry.title, "link" : entry.link , "saved_at" : datetime.now()})
			except:
				self.errors.append(" Error in title or link")
			try:
				item["author"] = entry.author
			except:
				item["author"] = ""
				self.errors.append(" Warning: no author")
			try:
				item["published_at_str"]  = entry.published
			except:
				self.errors.append(" Error in published")
			try:
				item["content_html"] = entry.description
			except:
				self.errors.append(" Error in content")
			try:
				# Only getting the link to the first element of the enclosure, it depends on how rss is formed and maybe podcast need to get more links
				item["enclosure"] = entry.enclosures[0]["href"]
			except:
				#self.errors.append(" Warning: no enclosure")
				item["enclosure"] = ""

			#item["content_text"] = html2text.html2text(item["content_html"])
			self.items.append(item)

		# Update last item time in feed info
		if new_last_time_item != 0:
			self.info["last_time_item"] = new_last_time_item

		return len(self.items)

	def enclosures(self):
		try:
			for item in self.items:
				self.db.download(self.info["name"],item["enclosure"])
		except:
			self.errors.append(" Error in enclosure download")
			return -1
		return 1

	def image_cache(self):
		for i in range(len(self.items)):
			try:
				image_url = self.items[i]["image-newspaper3k"]
				if image_url == "":
					image_url = self.items[i]["image-opengraph"]
				image_filename = image_download_create_thumbnails(image_url,self.info["name"])
				self.items[i]["image_cache"] = image_filename
			except Exception as e:
				self.errors.append(" Error in image_cache: "+str(e))
				self.items[i]["image_cache"] = ""
		return 0

	def post_to_wp(self):
		for item in self.items:
			image = None
			if "image-opengraph" in item:
				image = item["image-opengraph"]
			post_to_wp.post(item["published_at_str"], item["title"],item["content_html"],item["full_text-newspaper3k"],self.info["collection"],item["link"],image)
		return 0

	def enhance_newspaper(self):
		for i in range(len(self.items)):
			if "link" in self.items[i]:
				try:
					article = Article(self.items[i]["link"])
					article.download()
					article.parse()
					self.items[i]["full_text-newspaper3k"] = article.text
					self.items[i]["image-newspaper3k"] = article.top_image
					self.items[i]["movies-newspaper3k"] = " ".join(article.movies)
				except Exception as e:
					self.errors.append(" Warn no Newspaper3K: " + str(e))
		return 0

	def enhance_opengraph(self):
		for i in range(len(self.items)):
			if "link" in self.items[i]:
				try:
					opengraph_item = opengraph.OpenGraph(url=self.items[i]["link"])
					self.items[i]["image-opengraph"] = opengraph_item.image
				except Exception as e:
					self.errors.append(" Warn no Opengraph: " + str(e))
		return 0

	def update_feed_info(self):
		aux = db.replace_one(ENV["DB_COLLECTION_SOURCES"],self.info["name"],self.info)
		#print(aux.matched_count)

	def store(self):
		if len(self.items) != 0:
			# Store all new items
			transaction_ids = self.db.store_many(self.info["collection"],self.items)

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
	def __init__(self,host,port,db_name):
		client = MongoClient(host, port)
		self.db = client[db_name]

	def store(self,collection,row):
		return self.db[collection].insert(row)

	def store_many(self,collection,rows):
		return self.db[collection].insert_many(rows)

	def read_all(self,collection):
		return self.db[collection].find()

	def replace_one(self,collection,name,row):
		return self.db[collection].replace_one({"name":name},row)

	def download(self,url_file):
		return "No download compatibility in this kind of db"

# Some parameters are useless but we keep they to have the same functions than the rest of the db objects (in the future we will make a strategy pattern to encapsulate everything under a parent class)
class DatabaseFile:
	def __init__(self,host,port,db_name):
		self.db = "../data/"+db_name + "/"

	# Function to append a json "manually" to a file to avoid load all the file and join and store
	def append_to_json(self,json_dump,path):
		with open(path, 'ab+') as f:
			f.seek(0,2)                                	#Go to the end of file
			if f.tell() == 0 :                         	#Check if file is empty
				f.write(json_dump.encode())  			#If empty, write an array
			else :
				f.seek(-1,2)
				f.truncate()                           	#Remove the last character, open the array
				f.write(' , '.encode())                	#Write the separator
				f.write(json_dump.encode())    			#Dump the dictionary
				f.write(']'.encode())

	def store(self,collection,row):
		self.append_to_json(json.dumps(row,default=str),self.db+collection+".json") # Default=str transform dates in str, wich is not recommended to use but solve the problem "TypeError: Object of type 'datetime' is not JSON serializable"
		return 1

	def store_many(self,collection,rows):
		self.append_to_json(json.dumps(rows,default=str)[1:-1],self.db+collection+".json") # [1:-1] remove the "[" and "]" to append fastly
		return 1

	def read_all(self,useless):
		result = []
		for file in os.listdir(self.db):
			if file.endswith(".conf"):
				with open(self.db+file) as f:
					data = json.load(f)
					data["name"] = file[:-5].replace(" ", "_") # The name of the feed should be the one in the filename
				result.append(data)
		return result

	def replace_one(self,collection,name,row):
		with open(self.db+name+".conf", "w") as myfile:
			myfile.write(json.dumps(row))
		return 1

	def download(self,collection,url_file):
		print("Try to downlod ", url_file)
		if not os.path.exists(self.db + collection):
			os.makedirs(self.db + collection)
		try:
			filename = url_file[url_file.rfind("/")+1:]
			file = wget.download(url_file)
			os.rename(file,self.db + collection+"/"+file)
		except Exception as e:
			print(str(datetime.now()) +" Error downloading with WGET: ",filename," e: ",e)
		finally:
			print(str(datetime.now()) +" Download finished ", file)
		return 1



###### MAIN ######

# Default ENV
default_env = {"DB_TYPE":"MONGODB","DB_NAME":"feeds","DB_COLLECTION_SOURCES":"0_sources","DB_HOST":"localhost","DB_PORT": "27017","THREADS":"1","DOWNLOAD":"OFF","IMAGE_CACHE":"OFF","POST_TO_WP":"ON"}
# Command line ENV
command_line_arguments = {}
# Operative System ENV
os_env = {key:value for key, value in os.environ.items() if (key in default_env)} # os_env get the environment vars only if they exist in the default env of the this program

# Command line argument parser
if __name__ == '__main__':
	parser = argparse.ArgumentParser(prog="rss_to_db",usage="rss_to_db [--variable value]",description='Check rss urls for new content and store it',epilog="Execution or rss_to_db finished!")
	for key in default_env:
		parser.add_argument("--"+key)
	args = parser.parse_args()
	command_line_arguments = {key:value for key, value in vars(args).items() if value}

# Generate ENV first with command line ENV, then Operative system ENV and last with default_env
ENV = ChainMap(command_line_arguments, os_env, default_env) # ENV is a special dict made by several dict, when access to a key, use the key with more priority if it exists

# DB Initialization
if ENV["DB_TYPE"] in ["FILE"] or ENV["DOWNLOAD"] == "ON":
	db = DatabaseFile("","",ENV["DB_NAME"])
elif ENV["DB_TYPE"] in ["MONGODB","MONGO"]:
	db = DatabaseMongo(ENV["DB_HOST"],  int(ENV["DB_PORT"]),ENV["DB_NAME"])
	# Initialize data
	if db.read_all(ENV["DB_COLLECTION_SOURCES"]).count() == 0:
		import insert_sources_in_db


# Execute the script
def execute():
	threads = int(ENV["THREADS"])
	if threads > 1:
		print(str(datetime.now()) + " # Execution (",threads," threads)")
		def exec_feed(source):
			Feed(source,db).run()
		with futures.ThreadPoolExecutor(max_workers=threads) as ex:
			sources = db.read_all(ENV["DB_COLLECTION_SOURCES"])
			results = ex.map(exec_feed, sources)
		print(str(datetime.now()) + " # Finished execution")
	else:
		print(str(datetime.now()) + " # Sequence execution")
		for source in db.read_all(ENV["DB_COLLECTION_SOURCES"]):
			Feed(source,db).run()

# Execution
execute()
