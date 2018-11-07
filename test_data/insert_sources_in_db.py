#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Init db with values un test_threads

import csv
from pymongo import MongoClient
import re

DB_NAME = "feeds"
COLLECTION_NAME_SOURCES = "0_sources"

client = MongoClient('localhost', 27017)[DB_NAME]


with open('sources.tsv') as file:
  for line in file:
      print(line)
      elements = re.findall(r'\S+', line)
      row = {"name":elements[0],"url":elements[1]}
      client[COLLECTION_NAME_SOURCES].insert(row)
