from typing import List, Any
from Model import Person


class Image:
    def __init__(self, path: str):
        # Parameters
        self.path = path

        # Other fields
        self.dbid: int = Any
        self.encodings_in_image: List
        self.matched_people = List[Person]

        self.exif_data = None
        # self.tech_quality: float = Any  # Technical quality (FUTURE)
        # self.ae_quality: float = Any # Aesthetic quality (FUTURE)

    def is_tracked(self) -> bool:
        """
        :return: Whether this file is in the database
        """
        return self.dbid is not None

    def save_tags(self):
        pass

    @staticmethod
    def from_db_row(row) -> "Image":
        """
        Create an Image instance from a database row
        :return:
        """
        pass

    def to_db_row(self):
        pass
