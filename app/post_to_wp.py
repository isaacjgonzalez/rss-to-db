# Post in wordpress through the REST API using Aplication password Plugin (https://wordpress.org/plugins/application-passwords/)
# Some insights about how to do it https://discussion.dreamhost.com/t/how-to-post-content-to-wordpress-using-python-and-rest-api/65166

import requests
import json
import base64
import urllib

from io import BytesIO

# Data to be filled with your configs:
user = 'rssbot'
pythonapp = 'VHXw Hkpz FoPZ TIYt r7Fu wWgE'
url = 'https://portal.agora.gal/wp-json/wp/v2'
author_id = 128

# Headers
data_string = user + ':' + pythonapp
token = base64.b64encode(data_string.encode())
headers = {'Authorization': 'Basic ' + token.decode('utf-8')}

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
