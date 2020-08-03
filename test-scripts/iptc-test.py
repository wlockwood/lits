from os import listdir
from os import path
import pyexiv2 as pe2
from pprint import pprint as pp
from Model.Image import Image

from Controllers.FaceRecognizer import encode_faces

scan_path = r"..\test-data\unknown"
images_to_scan = [Image(path.join(scan_path, f)) for f in listdir(scan_path)
                  if path.isfile(path.join(scan_path, f))]


image = Image(r"..\test-data\unknown\sam tongue out.jpg")

print("Reading file ", image.filepath)
with open(image.filepath, 'rb+') as file:
    with pe2.ImageData(file.read()) as imdat:
        data = imdat.read_iptc(encoding=Image.normal_encoding)
pp(data)

