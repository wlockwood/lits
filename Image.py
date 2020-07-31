from typing import List, Any
import Person

class Image:
    def __init__(self, path: str):
        # Parameters
        self.path = path

        # Other fields
        self.dbid: int = Any
        self.encodings_in_image: List
        self.matched_people = List[Person]

        self.exif_data = None
        self.tech_quality: float = Any  # Technical quality
        self.ae_quality: float = Any # Aesthetic quality

    def is_tracked(self) -> bool:
        """
        :return: Whether this file is in the database
        """
        return self.dbid is not None

