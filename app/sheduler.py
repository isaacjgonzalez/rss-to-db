#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import schedule
import time

def job():
    import rss_to_db


schedule.every().hour.do(job)


while True:
    schedule.run_pending()
    time.sleep(1)
