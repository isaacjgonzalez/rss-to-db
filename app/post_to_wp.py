# Post in wordpress through the REST API using Aplication password Plugin (https://wordpress.org/plugins/application-passwords/)
# Some insights about how to do it https://discussion.dreamhost.com/t/how-to-post-content-to-wordpress-using-python-and-rest-api/65166

import os
import requests
import json
import base64
import io
import urllib.request
import mysql.connector
from datetime import datetime

# This load the config
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
    image_id = None
    if not image_url == None:
        image_filename = image_url.split('/')[-1]
        image_filename = folder+image_filename
        urllib.request.urlretrieve(image_url, image_filename)
        media = { 'file': open(image_filename,'rb'),'caption': title}
        image_request = requests.post(url + '/media', headers=headers, files=media)
        if image_request.status_code == 201:
            image_id = json.loads(image_request.content)['id']

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

    post_request = requests.post(url + '/posts', headers=headers, json=post)

    if post_request.status_code == 201:
        return json.loads(post_request.content.decode('utf-8'))['id']
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

categorias = {"Cultura":"4","Cinema":"5","Literatura":"6","Culinaria":"7","Ensino":"8","Lecer":"9","Humor":"10","Historia":"11","Música":"12","Divulgación":"13","Tecnoloxía":"14","Deporte":"15","Tendencias":"16","Ciencia":"17","Principal":"18","Superior":"19"}

def post(published_at_str, title, excerpt, content, category, url, image_url=None):
    if category in categorias.keys():
        number_of_categories = [categorias[category]]
    else:
        number_of_categories = [13]

    id = post_to_wp(published_at_str, title, excerpt, content, number_of_categories, image_url)
    add_link_to_post(id,url)



if __name__ == '__main__':
    # Example
    post("Chegou Podgalego","Resumo","Contido",[13],"https://isaacgonzalez.eu/imaxes/capura_podgalego.png","https://podgalego.agora.gal")
