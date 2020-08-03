# Builtins
from typing import List, Any, Dict
import unittest

# External modules
import jsonpickle
import numpy
from numpy.core.multiarray import ndarray
import pyexiv2 as pe2

# Custom code


class Image:
    encoding_store_field_name = "Xmp.dc.face_encodings"  # Custom tag. Unsure on the dc (Dublin Core) namespace
    keyword_field_name = "Iptc.Application2.Keywords"
    normal_encoding = "ISO-8859-1"  # Single-byte unicode approximation

    def __init__(self, path: str, skip_md_init: bool = False):
        """
        :param path: Path to an image file
        :param skip_md_init: Skip initializing metadata. Mostly for unit tests.
        """
        # Parameters
        self.path = path

        # Other fields
        self.extension = self.path.split(".")[-1]
        self.dbid: int = Any
        self.encodings_in_image: List[ndarray] = []
        self.matched_people: List[Person] = []

        # Metadata fields
        self.md_init_complete = False
        self.iptc: Dict = {}
        self.exif: Dict = {}
        self.xmp: Dict = {}
        self.init_metadata()

        # Look for existing face encodings
        if self.encoding_store_field_name in self.xmp:
            self.encodings_in_image = self.get_encodings_from_metadata()

        # self.tech_quality: float = Any  # Technical quality (FUTURE)
        # self.ae_quality: float = Any # Aesthetic quality (FUTURE)

    def __str__(self):
        return self.path

    def __repr__(self):
        f"Image ({str(self)})"

    def is_tracked(self) -> bool:
        """
        :return: Whether this file is in the database
        """
        return self.dbid is not None

    def init_metadata(self):
        """
        Load IPTC metadata for this image.
        :return: Fields with data in them.
        """
        file = pe2.Image(self.path)
        self.iptc = file.read_iptc(encoding=self.normal_encoding)
        self.exif = file.read_exif(encoding=self.normal_encoding)
        self.xmp = file.read_xmp(encoding=self.normal_encoding)
        file.close()
        self.md_init_complete = True

    def get_keywords(self) -> List[str]:
        if not self.md_init_complete:
            self.init_metadata()
        field_data = self.iptc.get("Iptc.Application2.Keywords", "")
        return field_data.split(",")


    def append_keywords(self, to_append: List[str]) -> int:
        """
        Appends a list of keywords to the keyword list after checking for duplicates.
        :param to_append: Keywords to append
        :return: Number of keywords that were appended.
        """
        if not self.md_init_complete:
            self.init_metadata()

        current = self.get_keywords()

        new_kws = 0
        if to_append not in current:
            current.append(to_append)
            new_kws += 1

        patch = {self.keyword_field_name: ",".join(current)}
        loaded = pe2.Image(self.path)
        loaded.modify_iptc(patch, encoding=Image.normal_encoding)
        loaded.close()

        return new_kws


    def set_encodings_in_metadata(self, encodings: List[ndarray]):
        """

        :return:
        """
        as_bytes = [str(enc.tobytes()) for enc in encodings]
        to_write = '\n'.join(as_bytes)

        # Write to file
        patch = {self.keyword_field_name: to_write}
        loaded = pe2.Image(self.path)
        loaded.modify_iptc(patch, encoding=Image.normal_encoding)
        loaded.close()


    def get_encodings_from_metadata(self, assign: bool = True) -> List[ndarray]:
        """
        Look in the comment field for a pydarray stored as bytes.
        :return: Found encoding as ndarray, or None if nothing found
        """
        if not self.md_init_complete:
            self.init_metadata()

        if self.encoding_store_field_name not in self.xmp:
            return None
        read_text = self.xmp[self.encoding_store_field_name]
        text_list = [bytes(string_form, encoding=self.normal_encoding) for string_form in read_text.split("\n")]
        list_e_bytes = [numpy.frombuffer(bytes, dtype="float64") for bytes in text_list]
        if assign:
            self.encodings_in_image = list_e_bytes
        return list_e_bytes



    @staticmethod
    def from_db_row(row) -> "Image":
        """
        Create an Image instance from a database row
        :return:
        """
        pass

    def to_db_row(self):
        pass

# Circular import
from Model import Person