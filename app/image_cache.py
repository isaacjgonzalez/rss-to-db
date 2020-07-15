from urllib.request import urlopen
from PIL import Image
import os
from datetime import datetime

sizes = [(1024,768),(800,600),(320,240),(160,120)]
formats = ["webp","png"]
folder = os.path.dirname(os.path.abspath(__file__)) + "/../data/image_cache/" # ended with /

if not os.path.exists(folder):
    os.makedirs(folder)

def image_download_create_thumbnails(image_url,sufix_filename=''):

    if image_url == "":
        return ""

    img = Image.open(urlopen(image_url))

    filename = datetime.now().strftime("%Y%m%d%H%M%S") + '-' + sufix_filename.replace(" ", "_").replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')

    if len(filename) > 40:
        filename = filename[0:40]

    for format in formats:
        for size in sizes:
            filename_local = folder + filename + '_' + str(size[0]) + '_' + str(size[1]) + '.' + format
            im1 = img.convert("RGB")
            im1.thumbnail(size)
            im1.save(filename_local,format)

    return filename
