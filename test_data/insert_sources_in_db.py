#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Init db with values un test_threads

import csv
from pymongo import MongoClient
import re
import os

DB_NAME = "feeds"
COLLECTION_NAME_SOURCES = "0_sources"
path = os.path.dirname(os.path.abspath(__file__))
db_port = os.environ['DB_PORT']
if db_port == "":
    db_port = 27017

client = MongoClient('localhost', db_port)[DB_NAME]


with open(path+'sources.tsv') as file:
  for line in file:
      print(line)
      elements = re.findall(r'\S+', line)
      row = {"name":elements[0],"url":elements[1]}
      client[COLLECTION_NAME_SOURCES].insert(row)
