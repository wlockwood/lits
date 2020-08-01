from typing import List, Any

from numpy.core.multiarray import ndarray

from Model.Image import Image

class Person:
    """An identified (name<->picture correlation) person."""

    def __init__(self, name: str, known_images: List[Image]):
        # Parameters
        self.name = name
        self.known_images = known_images

        # Other fields
        self.encoding: ndarray = Any
        self.dbid: int = Any

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Person({str(self)}"

    @staticmethod
    def from_db_row(row) -> "Person":
        pass
