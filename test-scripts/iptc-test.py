from os import listdir
from os import path
import pyexiv2 as pe2
from pprint import pprint as pp
from Model.ImageFile import ImageFile

scan_path = r"..\test-data\unknown"
images_to_scan = [ImageFile(path.join(scan_path, f)) for f in listdir(scan_path)
                  if path.isfile(path.join(scan_path, f))]


image = ImageFile(r"..\test-data\unknown\sam tongue out.jpg")

for image in images_to_scan:
    print("Reading file ", image.filepath)
    with open(image.filepath, 'rb+') as file:
        with pe2.ImageData(file.read()) as imdat:
            data = imdat.read_exif(encoding=ImageFile.normal_encoding)
            print(data.get("Exif.Photo.ISOSpeedRatings"))