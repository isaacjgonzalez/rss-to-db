# Post in wordpress through the REST API using Aplication password Plugin (https://wordpress.org/plugins/application-passwords/)
# Some insights about how to do it https://discussion.dreamhost.com/t/how-to-post-content-to-wordpress-using-python-and-rest-api/65166

import requests
import json
import base64
<<<<<<< HEAD
import io
import urllib.request
import mysql.connector


# This load the config
from post_to_wp_config import *

=======
import urllib

from io import BytesIO

# Data to be filled with your configs:
user = 'rssbot'
pythonapp = 'VHXw Hkpz FoPZ TIYt r7Fu wWgE'
url = 'https://portal.agora.gal/wp-json/wp/v2'
author_id = 128
>>>>>>> 96600694af1df8516c995f8e2a9da0a9d171738a

# Headers
data_string = user + ':' + pythonapp
token = base64.b64encode(data_string.encode())
headers = {'Authorization': 'Basic ' + token.decode('utf-8')}

<<<<<<< HEAD
def post_to_wp(title, excerpt, content, categories, image_url=None):
    image_id = None
    if not image_url == None:
        image_extension = image_url.split('.')[-1]
        image_filename = "../data/image_cache/0_tmp_image."+image_extension
        urllib.request.urlretrieve(image_url, image_filename)
        media = { 'file': open(image_filename,'rb'),'caption': title}
        image_request = requests.post(url + '/media', headers=headers, files=media)
        if image_request.status_code == 201:
            image_id = json.loads(image_request.content)['id']

    post = {
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

def add_link_to_post(post_id,link_to):
    mydb = mysql.connector.connect(host=dbhost,
                                         database=dbdatabase,
                                         user=dbuser,
                                         password=dbpasswd)
    mycursor = mydb.cursor()
    sql = "SELECT meta_id FROM `wp_5_postmeta` ORDER BY meta_id DESC LIMIT 1 "
    mycursor.execute(sql)
    last_id = int(mycursor.fetchone()[0])

    mycursor = mydb.cursor()
    sql = "INSERT INTO wp_5_postmeta (meta_id, post_id, meta_key, meta_value) VALUES (%s, %s, %s, %s)"
    val = (last_id+1,post_id, "_links_to",link_to)
    mycursor.execute(sql, val)

    mycursor = mydb.cursor()
    sql = "INSERT INTO wp_5_postmeta (meta_id, post_id, meta_key, meta_value) VALUES (%s, %s, %s, %s)"
    val = (last_id+2,post_id, "_links_to_target","_blank")
    mycursor.execute(sql, val)

    mydb.commit()


id = post_to_wp("Chegou Podgalego","Resumo","Contido",[13],"https://isaacgonzalez.eu/imaxes/capura_podgalego.png")
print(id)
add_link_to_post(id,"https://podgalego.agora.gal")
=======
#def post(title, excerpt, content, categories, url_img)
#media = { 'file': open('eyes-1221663_1280-1038x548.jpg','rb'),
#            'caption': 'My great demo picture'}

image_url = "https://espello.gal/wp-content/uploads/2019/11/eyes-1221663_1280-1038x548.jpg"
media = { 'file': BytesIO(requests.get(image_url).content),
            'caption': 'My great demo picture'}

image = requests.post(url + '/media', headers=headers, files=media)
print(image)
print(image.content)
image_id = json.loads(image.content)['id']
print('Your image id is ' + str(image_id))




post = {
		'title': 'First REST API post',
		'excerpt': 'Exceptional post!',
		'content': 'this is the content post',
		'author': author_id,
		'format': 'standard',
        'status': 'publish',
		'categories':[13],
        'featured_media':image_id
		}

r = requests.post(url + '/posts', headers=headers, json=post)

print(r)
print(json.loads(r.content.decode('utf-8'))['link'])
>>>>>>> 96600694af1df8516c995f8e2a9da0a9d171738a
