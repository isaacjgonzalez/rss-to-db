#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Init db with values un test_threads

from pymongo import MongoClient
import re
import os

# Insert values in csv file (separated by tab) and use the position in each row to get name, collection (if not available place -1) and feed_url
def insert_sources_in_db(filename,name_position,collection_position,feed_url_position):

    path = os.path.dirname(os.path.abspath(__file__))
    #print(path)

    if 'DB_NAME' in os.environ:
        DB_NAME = os.environ['DB_NAME']
    else:
        DB_NAME = "feeds"
    if 'DB_PORT' in os.environ:
        db_port = int(os.environ['DB_PORT'])
    else:
        db_port = 27017
    if 'DB_HOST' in os.environ:
        db_host = os.environ['DB_HOST']
    else:
        db_host = '0.0.0.0'
    if 'COLLECTION_NAME_SOURCES' in os.environ:
        COLLECTION_NAME_SOURCES = os.environ['COLLECTION_NAME_SOURCES']
    else:
        COLLECTION_NAME_SOURCES = "0_sources"
    print("Conecting to db...  Host: "+str(db_host)+" port: "+str(db_port))
    client = MongoClient(db_host, db_port)[DB_NAME]

    i = 0
    with open(path+'/../data/'+filename) as file:
      for line in file:
          elements = re.split(r'\t', line)
          if collection_position < 0:
              row = {"name":elements[name_position],"url":elements[feed_url_position]}
          else:
              row = {"name":elements[name_position],"collection":elements[collection_position],"url":elements[feed_url_position]}
          print(row)
          client[COLLECTION_NAME_SOURCES].insert_one(row)
          i+=1
    print(str(i) + " sources added to db in initialization")

## MAIN ##
if not os.path.exists('../config/sources.tsv'=:
    print("ERROR: I can't read /config/sources.tsv file, please be sure it exists or I can read it!")
else:
    insert_sources_in_db('../config/sources.tsv',2,3,0)
