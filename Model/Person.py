from typing import List, Any

from numpy.core.multiarray import ndarray
from Model.FaceEncoding import FaceEncoding

class Person:
    """A person who is tracked in the database, which must include one or more DB-tracked face encodings."""

    def __init__(self, person_id: int, name: str, encodings: List[FaceEncoding]):
        # Parameters
        self.dbid = person_id
        self.name = name

        # Other fields
        self.encodings: List[FaceEncoding] = encodings

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Person({self.dbid}: {str(self)})"