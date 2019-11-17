#!/usr/bin/python3
# -*- coding: utf-8 -*-

import schedule
import time

import rss_to_db



def job():
    rss_to_db.execute()
    import export_to_json


schedule.every().hour.do(job)


# First execution
print("First execution")
rss_to_db.execute()
# Sheduled execution
while True:
    schedule.run_pending()
    time.sleep(1)
