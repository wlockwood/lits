from iptcinfo3 import IPTCInfo
from pprint import pprint as pp

info = IPTCInfo("..\\test-data\\unknown\\sam keyword and title.jpg", inp_charset="utf_8", out_charset="utf_8")
keys = ['object name', 'edit status', 'editorial update', 'urgency', 'subject reference', 'category', 'supplemental category', 'fixture identifier', 'keywords', 'content location code', 'content location name', 'release date', 'release time', 'expiration date', 'expiration time', 'special instructions', 'action advised', 'reference service', 'reference date', 'reference number', 'date created', 'time created', 'digital creation date', 'digital creation time', 'originating program', 'program version', 'object cycle', 'by-line', 'by-line title', 'city', 'sub-location', 'province/state', 'country/primary location code', 'country/primary location name', 'original transmission reference', 'headline', 'credit', 'source', 'copyright notice', 'contact', 'caption/abstract', 'local caption', 'writer/editor', 'image type', 'image orientation', 'language identifier', 'custom1', 'custom2', 'custom3', 'custom4', 'custom5', 'custom6', 'custom7', 'custom8', 'custom9', 'custom10', 'custom11', 'custom12', 'custom13', 'custom14', 'custom15', 'custom16', 'custom17', 'custom18', 'custom19', 'custom20']

for key in keys:
    if info[key]:
        print(f"key {key:15} = {info[key]}")




