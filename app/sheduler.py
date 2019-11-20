#!/usr/bin/python3
# -*- coding: utf-8 -*-

import schedule
import time

import rss_to_db
import export_to_json


def job():
    rss_to_db.execute()
    export_to_json.export()


schedule.every().hour.do(job)


# First execution
#print("First execution")
#rss_to_db.execute()
#import export_to_json
# Sheduled execution
while True:
    schedule.run_pending()
    time.sleep(1)
