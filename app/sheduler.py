#!/usr/bin/python3
# -*- coding: utf-8 -*-

import schedule
import time

import rss_to_db



def job():
    import rss_to_db


schedule.every().hour.do(job)


while True:
    schedule.run_pending()
    time.sleep(1)
