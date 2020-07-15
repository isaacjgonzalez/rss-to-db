# Post in wordpress through the REST API using Aplication password Plugin (https://wordpress.org/plugins/application-passwords/)
# Some insights about how to do it https://discussion.dreamhost.com/t/how-to-post-content-to-wordpress-using-python-and-rest-api/65166

import os
import requests
import json
import base64
import io
import urllib.request
import urllib.parse
import mysql.connector
from datetime import datetime
from dateutil import parser


# This load the config

import sys
sys.path.insert(0, '../config/')
from post_to_wp_config import *


# Headers
data_string = user + ':' + pythonapp
token = base64.b64encode(data_string.encode())
headers = {'Authorization': 'Basic ' + token.decode('utf-8')}
# Folder cache
folder = "../data/image_cache_wp/"
if not os.path.exists(folder):
    os.makedirs(folder)

def post_to_wp(published_at_str, title, excerpt, content, categories, image_url=None):
    #print(published_at_str, title, excerpt, content, categories, image_url)
    image_id = None
    if not image_url == None:
        image_filename = image_url.split('/')[-1]
        image_filename = folder+image_filename
        # Convert UTF8 url to escaped url: https://stackoverflow.com/questions/4389572/how-to-fetch-a-non-ascii-url-with-python-urlopen
        aux_url = urllib.parse.urlsplit(image_url)
        aux_url = list(aux_url)
        aux_url[2] = urllib.parse.quote(aux_url[2])
        image_url = urllib.parse.urlunsplit(aux_url)
        try:
            urllib.request.urlretrieve(image_url, image_filename)
            media = { 'file': open(image_filename,'rb'),'caption': title}
            image_request = requests.post(wpapi_url + '/media', headers=headers, files=media)
            if image_request.status_code == 201:
                image_id = json.loads(image_request.content)['id']
        except Exception as e:
            print("Error in post_to_wp at image retrive: ",e)

    post = {
            'date': published_at_str,
    		'title': title,
    		'excerpt': excerpt,
    		'content': content,
    		'author': author_id,
    		'format': 'standard',
            'status': 'publish',
    		'categories':categories
    		}

    if image_id != None:
        post['featured_media'] = image_id

    post_request = requests.post(wpapi_url + '/posts', headers=headers, json=post)

    if post_request.status_code == 201:
        return json.loads(post_request.content.decode('utf-8'))['id']
    print("Error in post_to_wp: ",post_request.status_code)
    return -1

# Function to add to add the custom permalink
def add_link_to_post(post_id,link_to):
    mydb = mysql.connector.connect(host=dbhost,
                                         database=dbdatabase,
                                         user=dbuser,
                                         password=dbpasswd)
    mycursor = mydb.cursor()
    sql = f"SELECT meta_id FROM {dbtable} ORDER BY meta_id DESC LIMIT 1 "
    mycursor.execute(sql)
    last_id = int(mycursor.fetchone()[0])

    mycursor = mydb.cursor()
    sql = f"INSERT INTO {dbtable} (meta_id, post_id, meta_key, meta_value) VALUES (%s, %s, %s, %s)"
    val = (last_id+1,post_id, "_links_to",link_to)
    mycursor.execute(sql, val)

    mycursor = mydb.cursor()
    sql = f"INSERT INTO {dbtable} (meta_id, post_id, meta_key, meta_value) VALUES (%s, %s, %s, %s)"
    val = (last_id+2,post_id, "_links_to_target","_blank")
    mycursor.execute(sql, val)

    mydb.commit()


def post(published_at_str, title, excerpt, content, category, url, image_url=None):
    if category in categorias.keys():
        number_of_categories = [categorias[category]]
    else:
        number_of_categories = [30] # Sen categoria

    published_at = parser.parse(published_at_str)

    id = post_to_wp(str(published_at), title, excerpt, content, number_of_categories, image_url)
    add_link_to_post(id,url)



if __name__ == '__main__':
    # Example
    post("Wed, 25 Jun 2020 17:49:24 +0000","TEST: Chegou Podgalego","Resumo","Contido","Cultura","https://podgalego.agora.gal","https://isaacgonzalez.eu/imaxes/capura_podgalego.png")
