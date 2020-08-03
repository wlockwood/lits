from typing import List, Any

from numpy.core.multiarray import ndarray


class Person:
    """An identified (name<->picture correlation) person."""

    def __init__(self, name: str):
        # Parameters
        self.name = name

        # Other fields
        self.encodings: List[ndarray] = []
        self.dbid: int = Any
        self.known_images: List[ImageFile] = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Person({str(self)}"


    @staticmethod
    def from_db_row(row) -> "Person":
        pass
        # This may end up being many DB rows

# Circular import
from Model.ImageFile import ImageFile