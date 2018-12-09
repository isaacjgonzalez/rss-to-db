#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Newspaper3k docker must be running

import requests
import json

def full_text(url):
    data = {"article":url}
    data_json = json.dumps(data)
    headers = {'Content-type': 'application/json'}
    r = requests.post(url="http://0.0.0.0:5000/article/text", data=data_json, headers=headers)
    return r.text

def imglink(url):
    data = {"article":url}
    data_json = json.dumps(data)
    headers = {'Content-type': 'application/json'}
    r = requests.post(url="http://0.0.0.0:5000/article/imglink", data=data_json, headers=headers)

    return r.text.strip('"')


print(full_text("https://espello.gal/2018/03/20/enfermidades-2-0/"))
print(imglink("https://espello.gal/2018/03/20/enfermidades-2-0/"))
