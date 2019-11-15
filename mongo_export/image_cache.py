from urllib.request import urlopen
from PIL import Image
import os

sizes = [(1024,768),(800,600),(320,240),(160,120)]
formats = ["webp","png"]
folder = "" # ended with /

image_url = "http://www.mazarelos.gal/wp-content/uploads/2019/10/guerriller@s.png"
img = Image.open(urlopen(image_url))

filename = os.path.basename(image_url).split(".")[0]

for format in formats:
    for size in sizes:
        filename_local = folder + filename + '_' + str(size[0]) + '_' + str(size[1]) + '.' + format
        im1 = img.convert("RGB")
        im1.thumbnail(size)
        im1.save(filename_local,format)
