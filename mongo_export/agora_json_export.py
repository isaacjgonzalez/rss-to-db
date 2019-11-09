#!/usr/bin/python3
# -*- coding: utf-8 -*-


from pymongo import MongoClient
from urllib.parse import urlparse
from bson.objectid import ObjectId
from bson import json_util
import pprint
import json

# Connect db
client = MongoClient('localhost', 27017)
db = client["feeds"]

# Get all categories
categories = set()
collection = db['0_sources']
for post in collection.find():
    categories.add(post["collection"])

# Generate exported info
exported_info = {}
for category in categories:
    # Sources of category
    sources_of_category = []
    for item in db['0_sources'].find({"collection":category}):
        url_feed = item["url"]
        url = urlparse(url_feed).scheme + "://" + urlparse(url_feed).hostname
        sources_of_category.append({"name":item["name"],"url":url,"url_feed":url_feed})

    # Posts of cateogories
    posts = []
    for post in db[category].find().sort("published_at_time",-1).limit(20):
        p = {}
        for key,value in post.items():
            if key in ["_id","saved_at"]:
                p[key] = json_util.dumps(value)
            else:
                p[key] = value
        posts.append(p)
    exported_info[category] = {"sources":sources_of_category,"posts":posts}


with open('agora_export.json', 'w') as fp:
    json.dump(exported_info, fp)
