# Builtins
from typing import List, Any
import unittest

# External libraries
import numpy
from numpy.core.multiarray import ndarray
from iptcinfo3 import IPTCInfo

# Custom code
from Model import Person

# Temporary
import os # related to bug in iptcinfo


class Image:
    encodings_in_image: List[ndarray]
    # Extracted from IPTCInfo
    iptc_field_list = ['object name', 'edit status', 'editorial update', 'urgency', 'subject reference', 'category',
            'supplemental category', 'fixture identifier', 'keywords', 'content location code', 'content location name',
            'release date', 'release time', 'expiration date', 'expiration time', 'special instructions',
            'action advised', 'reference service', 'reference date', 'reference number', 'date created', 'time created',
            'digital creation date', 'digital creation time', 'originating program', 'program version', 'object cycle',
            'by-line', 'by-line title', 'city', 'sub-location', 'province/state', 'country/primary location code',
            'country/primary location name', 'original transmission reference', 'headline', 'credit', 'source',
            'copyright notice', 'contact', 'caption/abstract', 'local caption', 'writer/editor', 'image type',
            'image orientation', 'language identifier', 'custom1', 'custom2', 'custom3', 'custom4', 'custom5',
            'custom6', 'custom7', 'custom8', 'custom9', 'custom10', 'custom11', 'custom12', 'custom13', 'custom14',
            'custom15', 'custom16', 'custom17', 'custom18', 'custom19', 'custom20']
    encoding_store_field_name = "caption/abstract"

    def __init__(self, path: str):
        # Parameters
        self.path = path

        # Other fields
        self.extension = self.path.split(".")[-1]
        self.dbid: int = Any
        self.encodings_in_image: List[ndarray] = []
        self.matched_people: List[Person] = []
        self.iptcinfo = None

        # self.exif_data = None = Any # (FUTURE)
        # self.tech_quality: float = Any  # Technical quality (FUTURE)
        # self.ae_quality: float = Any # Aesthetic quality (FUTURE)

    def is_tracked(self) -> bool:
        """
        :return: Whether this file is in the database
        """
        return self.dbid is not None

    def init_iptc(self) -> int:
        """
        Load IPTC metadata for this image.
        :return: Fields with data in them.
        """
        self.iptcinfo = IPTCInfo(self.path, force=True)
        # Fields with data
        return len([self.iptcinfo[x] is not None for x in self.iptc_field_list])

    def get_keywords(self):
        if self.iptcinfo == None:
            self.init_iptc()

        return self.iptcinfo["keywords"]

    def append_keyword(self, to_append: str) -> bool:
        """
        Appends one keyword to the keyword list.
        :param to_append: Keyword to append
        :return: Whether the keyword was new (True) or already existed (False)
        """
        if self.iptcinfo == None:
            self.init_iptc()
        if to_append not in self.iptcinfo["keywords"]:
            self.iptcinfo["keywords"].append(to_append)
            return True
        return False

    def set_encoding_in_metadata(self, encodings: List[ndarray]):
        """

        :return:
        """
        as_bytes = [str(enc.tobytes()) for enc in encodings]
        to_write = '\n'.join(as_bytes)
        self.iptcinfo[self.encoding_store_field_name] = to_write


    def get_encodings_from_metadata(self) -> List[ndarray]:
        """
        Look in the comment field for a pydarray stored as bytes.
        :return: Found encoding as ndarray, or None if nothing found
        """
        try:
            read_text = self.iptcinfo[self.encoding_store_field_name]
            list_e_bytes = [numpy.frombuffer(bytes, dtype="float64") for bytes in read_text.split("\n")]
            return list_e_bytes
        except Exception:
            return None

    def save_iptc(self):
        self.iptcinfo.save_as(self.path)

        # This is due to a bug in iptcinfo3: https://github.com/jamesacampbell/iptcinfo3/issues/22
        try:
            os.remove(self.path + "~")
        except OSError:
            pass


    @staticmethod
    def disable_iptc_errors() -> None:
        """
        Makes iptcinfo3's extraneous error messages not display during normal operation.
        Should be called exactly once prior to any usage of iptcinfo3
        """
        # Taken from https://stackoverflow.com/questions/50407738/python-disable-iptcinfo-warning
        import logging
        iptcinfo_logger = logging.getLogger('iptcinfo')
        iptcinfo_logger.setLevel(logging.ERROR)


    @staticmethod
    def from_db_row(row) -> "Image":
        """
        Create an Image instance from a database row
        :return:
        """
        pass

    def to_db_row(self):
        pass

class TestImage(unittest.TestCase):
    test_image = Image("..\\test-data\\unknown\\sam tongue out.jpg")
    test_encoding = numpy.frombuffer(b'\x00\x00\x00\xc0\x11\xc1\xb3\xbf\x00\x00\x00@Z\xdf\x9a?\x00\x00\x00\xe0\xc6\xd4\xae?\x00\x00\x00\xa0\xfe\x14\xbf\xbf\x00\x00\x00\x00\xd5^\xc4\xbf\x00\x00\x00\xc0\nx~\xbf\x00\x00\x00\xc0\x1f\xd4\x96\xbf\x00\x00\x00 o\x12\xc1\xbf\x00\x00\x00\x80t!\xb4?\x00\x00\x00\xa0L\x8d\xcd\xbf\x00\x00\x00`\xe6"\xc7?\x00\x00\x00\x006\xc3\x83?\x00\x00\x00\x80\x82\xb9\xd0\xbf\x00\x00\x00\xe0\xb2P\xa4?\x00\x00\x00\xc0\x08t\xb2?\x00\x00\x00\xe0\x13L\xcd?\x00\x00\x00`Xm\xc4\xbf\x00\x00\x00\xc0$+\xc8\xbf\x00\x00\x00\xe0T$\xc6\xbf\x00\x00\x00`pP\xb2\xbf\x00\x00\x00\xc0a\x1d\xa8\xbf\x00\x00\x00\xc0: \xb8?\x00\x00\x00@\xc7e\xa5\xbf\x00\x00\x00\x00\x1d\xab\xb2?\x00\x00\x00\xc0yo\xae\xbf\x00\x00\x00\xe0\x0e\x9f\xce\xbf\x00\x00\x00\xc0j\xb4\xad\xbf\x00\x00\x00\x00\x8a\xd1\xa2\xbf\x00\x00\x00@gA\x9b?\x00\x00\x00\x00p\x89D\xbf\x00\x00\x00\xa0YI\x9f\xbf\x00\x00\x00 \xe7"\xb2?\x00\x00\x00`\xb8|\xb0\xbf\x00\x00\x00`&\x01\xb9?\x00\x00\x00\x00\xd9E\xb9?\x00\x00\x00\x00\x9e2\xac?\x00\x00\x00\xe0\xbd\x8e\xba\xbf\x00\x00\x00\xe0\xe4\x8f\xc1\xbf\x00\x00\x00 }=\xd0?\x00\x00\x00\x00\x90k\xa4?\x00\x00\x00\xa0\x07\x05\xd0\xbf\x00\x00\x00\x00\xce3\xac\xbf\x00\x00\x00\x00\x84\xa9\xb1?\x00\x00\x00@t\x8f\xc9?\x00\x00\x00 \xdb\xea\xc9?\x00\x00\x00\xc0Ch\x94\xbf\x00\x00\x00\xc0*\xdd\x89?\x00\x00\x00\xc0\\\x99\xb7\xbf\x00\x00\x00\xc0xD\xc4?\x00\x00\x00\xe0!\xd4\xd3\xbf\x00\x00\x00 `\xd1\x9e?\x00\x00\x00\x80w\x9c\xc3?\x00\x00\x00\xc0\xb1\xb0\xa3?\x00\x00\x00\x80\xc1-\xb8?\x00\x00\x00@\xe3\x16\xb0?\x00\x00\x00\xc0\xee\xf2\xcc\xbf\x00\x00\x00\xe0\xbc\xc7\xb6?\x00\x00\x00@\xca\xf7\xba?\x00\x00\x00 \xfcn\xc5\xbf\x00\x00\x00\x80p:e?\x00\x00\x00\x80Ma\xb7?\x00\x00\x00\x00>\xec\xc7\xbf\x00\x00\x00`\x0f+\x9c\xbf\x00\x00\x00\xc0\xba\x1d\xb1\xbf\x00\x00\x00`4\x17\xcf?\x00\x00\x00\xe0\x1fZ\xb6?\x00\x00\x00\x00BA\xc2\xbf\x00\x00\x00\x80.\xf4\xc5\xbf\x00\x00\x00\xc0+=\xc4?\x00\x00\x00\x80\xe8\xee\xc4\xbf\x00\x00\x00`]\xd6\xc2\xbf\x00\x00\x00@\x13\x0b\x8c?\x00\x00\x00`>\xa8\xc5\xbf\x00\x00\x00`\xb1\xe0\xc2\xbf\x00\x00\x00\xe0tM\xd0\xbf\x00\x00\x00\xe0UO\x9e\xbf\x00\x00\x00 \x02\x14\xd6?\x00\x00\x00`\xb6\x14\xca?\x00\x00\x00\xc0\xfa\xed\xc4\xbf\x00\x00\x00\xe0&\xee\xad?\x00\x00\x00\xe0+#\x9b\xbf\x00\x00\x00\x00\x04\x9e\x94\xbf\x00\x00\x00\x00"\xd9\xbf?\x00\x00\x00 \xd3d\xbe?\x00\x00\x00`\xb0x\xa8\xbf\x00\x00\x00\xe0\x117\xbb\xbf\x00\x00\x00\xe0W~\xb7\xbf\x00\x00\x00\x80\xf6M\x9c\xbf\x00\x00\x00`2j\xce?\x00\x00\x00\xc0aR\xb2\xbf\x00\x00\x00\x00\x18\xa6|?\x00\x00\x00\x00\x04\xb9\xd0?\x00\x00\x00\x80_|\xa4?\x00\x00\x00\xa0c\x0c\x93?\x00\x00\x00\xe0\xcah\x98?\x00\x00\x00\x00\xbd\xebs?\x00\x00\x00\x00\xd3\xe1\xb3\xbf\x00\x00\x00\xa0\xfd\x84\xab\xbf\x00\x00\x00\x80\x0b\xd1\xbf\xbf\x00\x00\x00\xc0\x8f\r\xa0\xbf\x00\x00\x00\xe0\xd9\xac\x84\xbf\x00\x00\x00\xa0\xa8\x95\xab\xbf\x00\x00\x00\xc0A;\xa4?\x00\x00\x00@\xbd\x0f\xc1?\x00\x00\x00\xc0$a\xc6\xbf\x00\x00\x00\xe0\xf3\xc7\xc9?\x00\x00\x00\xc0\xfa9\xa5\xbf\x00\x00\x00\x80\x88\xb1\x9d?\x00\x00\x00\x00\xc3<\x82\xbf\x00\x00\x00\x00\xc2Kk\xbf\x00\x00\x00\xc0g\x01\xc2\xbf\x00\x00\x00\xc0\xc1\xf3\xac\xbf\x00\x00\x00\x80\xf7\xb8\xbe?\x00\x00\x00@\x90\xe5\xc4\xbf\x00\x00\x00@\xf6\xdf\xc3?\x00\x00\x00`\xce\x19\xc8?\x00\x00\x00\x80\\\xd5\xb7?\x00\x00\x00\xa0\x90\xeb\xbb?\x00\x00\x00\x80\xcb\xa8\xc2?\x00\x00\x00\x80\xd8_\xb3?\x00\x00\x00\xc0E\xed\x98\xbf\x00\x00\x00\xc0\x86A\x9c\xbf\x00\x00\x00\x00\x17\x9a\xcc\xbf\x00\x00\x00\x80\xba\x91\xb1\xbf\x00\x00\x00\x80j6\xbe?\x00\x00\x00\xe0>\x89w?\x00\x00\x00\xc0\x0f*\xa4?\x00\x00\x00\xa0xH\xb4?', dtype="float64")

    def test_rw_cycle(self):
        self.test_image.init_iptc()
        self.test_image.set_encoding_in_metadata(self.test_encoding)
        self.test_image.save_iptc()

        readout = self.test_image.get_encodings_from_metadata()
        all_match = True
        for i in range(len(self.test_encoding)):
            if self.test_encoding[i] != readout[i]:
                all_match = False
                break
        self.assertEqual(True, all_match, "test array doesn't match itself after having been written to and from file")
