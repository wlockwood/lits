from typing import List, Any
from collections import namedtuple
from numpy.core.multiarray import ndarray #Encoded faces

from Model.Person import Person
from Model.Image import Image
import face_recognition as fr
from dlib import resize_image

import unittest

# Named tuple to make later code more self documenting
ComparedFace = namedtuple("ComparedFace", "Person Distance")
ComparedFace.__str__ = lambda self: f"{self.Person.Name} ({self.Distance:.3f})"

def encode_faces(images: List[Image], jitter: int = 1, resize_to: int = 750):
    """

    :param images: A list of image paths to encode the faces of
    :param jitter: How many times to transform a face. Higher number is slower but more accurate.
    :param resize_to: Size to resize to. Lower number is faster but less accurate.
    :return:
    """

    encoded_faces = []
    for image in images:
        scale_factor = resize_to / max(image.shape[0], image.shape[1])
        new_x, new_y = int(round(image.shape[0] * scale_factor)), \
                       int(round(image.shape[1] * scale_factor))
        resized = resize_image(image, rows=new_y, cols=new_x)

        known_image = fr.load_image_file(image)
        image.encodings_in_image = fr.face_encodings(known_image, num_jitters=jitter, model="large")
    return images

def match_best(known_people: List[Person], unknown_encodings: List[ndarray], tolerance: float = 0.6) -> List[Person]:
    """
    Compares encoded versions of faces found in a picture to a set of known people and returns the best matches.
    :param known_people: List of identified Person objects.
    :param unknown_encodings: List of encoded representations of faces.
    :param tolerance: Maximum distance for a face to match at. Lower values result in stricter matches.
    :return: People objects that are the best matches for faces in unknown_encodings
    """
    # Track actual results
    found_people: List[Person] = []

    # Actual facial recognition logic
    for face in unknown_encodings:
        compare_results = fr.face_distance([x.Encoding for x in known_people], face)

        # Filter list step by step. I broke this into multiple lines for debugging.
        possible_matches = [ComparedFace(known_people[i], compare_results[i]) for i in range(len(compare_results))]

        # Remove faces that too unlike the face we're checking.
        possible_matches: List[ComparedFace] = [x for x in possible_matches if x.Distance < tolerance]

        # Removing already-found people
        possible_matches = [x for x in possible_matches if x.Person not in found_people]

        # Sort by chance of facial distance ascending (best matches first)
        possible_matches = sorted(possible_matches, key=lambda x: x.Distance)

        if len(possible_matches) > 0:
            best_match = possible_matches[0].Person
            # print(f"\tBest match: {str(possible_matches[0])}")  # DEBUG
            found_people.append([x for x in known_people if x.Name == best_match[0]][0])
    return found_people


# https://github.com/ageitgey/face_recognition/blob/master/examples/find_faces_in_batches.py
def FindFaces(images: List[str]):
    """
    NOT YET IMPLEMENTED. Detect faces in batches using the GPU, which should be 3x faster according to the docs.
    :param images:
    :return:
    """
    raise Exception("Batch face detection not yet implemented")
    pass

# Tests
class TestFaceRecogizer(unittest.TestCase):
    def setUp(self):
        known_image = Image("test-data\\known\\will.jpg")
        test_faces = encode_faces([known_image])
        test_person = Person("will", [known_image])
        test_person.encoding = test_faces[0]

    def test_match(self):
        pass

if __name__ == "__main__":
    pass