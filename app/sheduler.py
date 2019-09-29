#!/usr/bin/python3
# -*- coding: utf-8 -*-

import schedule
import time

import rss_to_db



def job():
    rss_to_db.execute()


schedule.every().hour.do(job)


# First execution
rss_to_db.execute()
# Sheduled execution
while True:
    schedule.run_pending()
    time.sleep(1)
