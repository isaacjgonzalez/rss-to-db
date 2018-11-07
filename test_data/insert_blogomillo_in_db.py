#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Init db with values un test_threads

import csv
from pymongo import MongoClient
import re
from urllib.parse import urlparse

DB_NAME = "feeds"
COLLECTION_NAME_SOURCES = "0_sources"

client = MongoClient('localhost', 27017)[DB_NAME]


with open('blogomillo.txt') as file:
  for line in file:
      #parsed_uri = urlparse(line)
      #name = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

      row = {"name":line,"url":line}
      #print(row)
      insertion_code = client[COLLECTION_NAME_SOURCES].insert(row)
      print(insertion_code)
