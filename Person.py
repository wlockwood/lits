from typing import List, Any

class Person:
    """An identified (name<->picture correlation) person."""
    def __init__(self, name: str, known_images: List[str]):
        # Parameters
        self.name = name
        self.known_images = known_images

        # Other fields
        self.encoding = Any
        self.dbid: int = Any

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Person({str(self)}"


    @staticmethod
    def from_db_row(row) -> "Person":
        pass

