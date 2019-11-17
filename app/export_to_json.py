#!/usr/bin/python3
# -*- coding: utf-8 -*-


from pymongo import MongoClient
from urllib.parse import urlparse
from bson.objectid import ObjectId
from bson import json_util
import pprint
import json
import os

# Connect db
COLLECTION_NAME_SOURCES = "0_sources"
if 'DB_NAME' in os.environ:
    db_name = os.environ['DB_NAME']
else:
    db_name = "feeds"
if 'DB_PORT' in os.environ:
    db_port = int(os.environ['DB_PORT'])
else:
    db_port = 27017
if 'DB_HOST' in os.environ:
    db_host = os.environ['DB_HOST']
else:
    db_host = '0.0.0.0'

client = MongoClient(db_host, db_port)
db = client[db_name]

# Get all categories
categories = set()
collection = db[COLLECTION_NAME_SOURCES]
for post in collection.find():
    categories.add(post["collection"])

# Generate exported info
exported_info = {}
for category in categories:
    # Sources of category
    sources_of_category = []
    for item in db[COLLECTION_NAME_SOURCES].find({"collection":category}):
        url_feed = item["url"]
        url = urlparse(url_feed).scheme + "://" + urlparse(url_feed).hostname
        sources_of_category.append({"name":item["name"],"url":url,"url_feed":url_feed})

    # Posts of cateogories
    posts = []
    for post in db[category].find().sort("published_at_time",-1).limit(20):
        p = {}
        for key,value in post.items():
            # Scape some json values
            if key in ["_id","saved_at"]:
                p[key] = json_util.dumps(value)
            else:
                p[key] = value
            # Cache image thumbnails


        posts.append(p)
    exported_info[category] = {"sources":sources_of_category,"posts":posts}

directory = "../data/export/"
if not os.path.exists(directory):
    os.makedirs(directory)

with open(directory+'agora_export.json', 'w') as fp:
    json.dump(exported_info, fp)
