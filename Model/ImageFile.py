# Builtins
from glob import glob
from typing import List, Any, Dict
from os import path, listdir

# External modules
from numpy.core.multiarray import ndarray
import pyexiv2 as pe2


class ImageFile:
    encoding_store_field_name = "Xmp.dc.Description"  # TODO: Extend pyexiv2 to support custom namespaces
    keyword_field_name = "Iptc.Application2.Keywords"
    normal_encoding = "ISO-8859-1"  # Single-byte unicode approximation

    def __init__(self, filepath: str, skip_md_init: bool = False):
        """
        :param filepath: Path to an image file
        :param skip_md_init: Skip initializing metadata. Mostly for unit tests.
        """
        # Parameters
        self.filepath = filepath

        # Other fields
        self.extension = self.filepath.split(".")[-1]
        self.dbid: int = -1
        self.encodings_in_image: List[ndarray] = []
        self.matched_people: List[Person] = []
        self.in_database = False

        # Metadata fields
        self.md_init_complete = False
        self.iptc: Dict = {}
        self.exif: Dict = {}
        self.xmp: Dict = {}
        if not skip_md_init:
            self.init_metadata()

        # self.tech_quality: float = Any  # Technical quality (FUTURE)
        # self.ae_quality: float = Any # Aesthetic quality (FUTURE)

    def __str__(self):
        return self.filepath

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
        file = pe2.Image(self.filepath)
        self.iptc = file.read_iptc(encoding=self.normal_encoding)
        self.exif = file.read_exif(encoding=self.normal_encoding)
        self.xmp = file.read_xmp(encoding=self.normal_encoding)
        file.close()
        self.md_init_complete = True

    def clear_keywords(self):
        patch = {self.keyword_field_name: ""}
        loaded = pe2.Image(self.filepath)
        loaded.modify_iptc(patch, encoding=ImageFile.normal_encoding)
        loaded.close()

        self.iptc[self.keyword_field_name] = ""

    def get_keywords(self, force_refresh: bool = False) -> List[str]:
        if not self.md_init_complete or force_refresh:
            self.init_metadata()

        field_data = self.iptc.get("Iptc.Application2.Keywords", "")
        return field_data.split(",") if len(field_data) > 0 else []


    def append_keywords(self, to_append: List[str]) -> int:
        """
        Appends a list of keywords to the keyword list after checking for duplicates.
        :param to_append: Keywords to append
        :return: Number of keywords that were appended.
        """
        if not self.md_init_complete:
            self.init_metadata()

        initial_kw: List[str] = self.get_keywords()
        current = initial_kw.copy()

        new_kws = 0
        for keyword in to_append:
            if keyword not in current:
                current.append(keyword)
                new_kws += 1
        if current == initial_kw:
            return 0

        current_string: str = ",".join(current)

        patch = {self.keyword_field_name: current_string}
        loaded = pe2.Image(self.filepath)
        loaded.modify_iptc(patch, encoding=ImageFile.normal_encoding)
        loaded.close()

        self.iptc[self.keyword_field_name] = current_string

        return new_kws

    @staticmethod
    def clear_keywords_bulk(folderpath: str):
        print(f"Trying to clear keywords in images found in {path.abspath(folderpath)}...")
        images_to_clear = glob(folderpath + "/**/" + "*.jpg", recursive=True)
        images_to_clear = [ImageFile(im) for im in images_to_clear]
        print(f"Found {len(images_to_clear):,} files to clear keywords from.")

        for im in images_to_clear:
            im.clear_keywords()
            print(f"Cleared {im.filepath}")
# Circular import
from Model import Person