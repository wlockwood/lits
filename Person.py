from typing import List

class Person:
    def __init__(self, name: str, known_images: List[str]):
        # Parameters
        self.name = name
        self.known_images = known_images

        # Other fields
        self.encoding = None