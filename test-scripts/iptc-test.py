from os import listdir
from os import path
from iptcinfo3 import IPTCInfo

from Model.Image import Image

scan_path = "..\\test-data\\unknown"
images_to_scan = [Image(path.join(scan_path, f)) for f in listdir(scan_path)
                  if path.isfile(path.join(scan_path, f))]

keys = ['object name', 'edit status', 'editorial update', 'urgency', 'subject reference', 'category',
        'supplemental category', 'fixture identifier', 'keywords', 'content location code', 'content location name',
        'release date', 'release time', 'expiration date', 'expiration time', 'special instructions', 'action advised',
        'reference service', 'reference date', 'reference number', 'date created', 'time created',
        'digital creation date', 'digital creation time', 'originating program', 'program version', 'object cycle',
        'by-line', 'by-line title', 'city', 'sub-location', 'province/state', 'country/primary location code',
        'country/primary location name', 'original transmission reference', 'headline', 'credit', 'source',
        'copyright notice', 'contact', 'caption/abstract', 'local caption', 'writer/editor', 'image type',
        'image orientation', 'language identifier', 'custom1', 'custom2', 'custom3', 'custom4', 'custom5', 'custom6',
        'custom7', 'custom8', 'custom9', 'custom10', 'custom11', 'custom12', 'custom13', 'custom14', 'custom15',
        'custom16', 'custom17', 'custom18', 'custom19', 'custom20']
Image.disable_iptc_errors()

for image in images_to_scan:
    print("Reading file ", image.path)
    info = IPTCInfo(image.path, inp_charset="utf_8", out_charset="utf_8")
    for key in keys:
        if info[key]:
            print(f"\tkey '{key:>25}' = {info[key]}")
