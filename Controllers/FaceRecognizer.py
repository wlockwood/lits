from typing import List, Any
from collections import namedtuple
from numpy.core.multiarray import ndarray  # Encoded faces

from Model.Person import Person
from Model.Image import Image
import face_recognition as fr
from dlib import resize_image

import unittest


def encode_faces(images: List[Image], jitter: int = 1, resize_to: int = 750) -> List[Image]:
    """
    Populates the encodings_in_image field of an Image
    :param images: A list of image paths to encode the faces of
    :param jitter: How many times to transform a face. Higher number is slower but more accurate.
    :param resize_to: Size to resize to. Lower number is faster but less accurate.
    :return: The input list of images.
    """
    # TODO: EXIF rotate images prior to encoding them

    encoded_faces = []
    for image in images:
        content = fr.load_image_file(image.path)
        scale_factor = resize_to / max(content.shape[0], content.shape[1])
        new_x, new_y = int(round(content.shape[0] * scale_factor)), \
                       int(round(content.shape[1] * scale_factor))
        resized = resize_image(content, rows=new_y, cols=new_x)

        image.encodings_in_image = fr.face_encodings(content, num_jitters=jitter, model="large")
    return images


# Named tuple to make matching code easier to read
ComparedFace = namedtuple("ComparedFace", "Person Distance")
ComparedFace.__str__ = lambda self: f"{self.Person.Name} ({self.Distance:.3f})"


def match_best(known_people: List[Person], unknown_encodings: List[ndarray], tolerance: float = 0.6) -> List[Person]:
    """
    Compares encoded versions of faces found in a picture to a set of known people and returns the best matches.
    :param known_people: List of identified Person objects.
    :param unknown_encodings: List of encoded representations of faces.
    :param tolerance: Maximum distance for a face to match at. Lower values result in stricter matches.
    :return: People objects that are the best matches for faces in unknown_encodings
    """
    if len(known_people) == 0:
        raise ValueError("match_best requires that at least one known person be specified")
    if type(known_people[0]) != Person:
        raise TypeError(f"known_people must be of type List[Person], but detected {type(known_people[0])}")
    if len(unknown_encodings) == 0:
        raise ValueError("match_best requires that at least one unknown image be specified")
    if type(unknown_encodings[0]) != ndarray:
        raise TypeError(f"unknown_encodings must be of type List[ndarray], but detected {type(unknown_encodings[0])}")

    # Flatten list of known people's encodings
    flat_known_encodings = []
    flat_known_people = []
    for kpers in known_people:
        flat_known_encodings.extend(kpers.encodings)
        flat_known_people.extend([kpers] * len(kpers.encodings))

    # Track actual results
    found_people: List[Person] = []

    # Actual facial recognition logic
    for face in unknown_encodings:
        compare_results = fr.face_distance(flat_known_encodings, face)

        # Filter list step by step. I broke this into multiple lines for debugging.
        possible_matches = [ComparedFace(flat_known_people[i], compare_results[i]) for i in range(len(compare_results))]

        # Remove faces that too unlike the face we're checking.
        possible_matches: List[ComparedFace] = [x for x in possible_matches if x.Distance < tolerance]

        # Removing already-found people
        possible_matches = [x for x in possible_matches if x.Person not in found_people]

        # Sort by chance of facial distance ascending (best matches first)
        possible_matches = sorted(possible_matches, key=lambda x: x.Distance)

        if len(possible_matches) > 0:
            best_match = possible_matches[0].Person
            found_people.append(best_match)
    return found_people


# https://github.com/ageitgey/face_recognition/blob/master/examples/find_faces_in_batches.py
def FindFaces(images: List[str]):
    """
    NOT YET IMPLEMENTED. Detect faces in batches using the GPU, which should be 3x faster according to the docs.
    :param images:
    :return:
    """
    raise NotImplementedError("Batch face detection not yet implemented")
    pass


# Tests
class TestFaceRecognizer(unittest.TestCase):
    test_data_path = "..\\test-data\\"
    known_images = [Image(test_data_path + "known\\will.jpg")]
    test_faces = encode_faces(known_images)
    test_person = Person("will")
    test_person.encodings = test_faces[0].encodings_in_image

    will_as_unknown = Image(test_data_path + "unknown\\will2.jpg")
    sam_will_trail = Image(test_data_path + "unknown\\sam will trail 2.jpg")
    mushroom = Image(test_data_path + "unknown\\mushroom.jpg")
    multiple_people = Image(test_data_path + "unknown\\work group will.jpg")
    different_person = Image(test_data_path + "unknown\\jackie phone.jpg")

    # Should match when same person
    def test_one_to_one_match(self):
        unknown_images = encode_faces([self.will_as_unknown])
        best_matches = match_best([self.test_person], unknown_images[0].encodings_in_image)
        self.assertEqual(len(best_matches), 1, "face didn't match itself in another picture")

    def test_multiple_pictures_per_known(self):
        # Requires more convoluted test setup for the known person
        known_images = [Image(self.test_data_path + "known\\will\\will.jpg"),
                        Image(self.test_data_path + "known\\will\\will sunglass hat.png")]
        encode_faces(known_images)
        test_person = Person("will", known_images)
        test_person.encodings = [enc for im in known_images for enc in im.encodings_in_image]  # Flat?

        unknown_images = encode_faces([self.will_as_unknown])
        best_matches = match_best([test_person], unknown_images[0].encodings_in_image)
        self.assertEqual(1, len(best_matches), "couldn't match a face using multiple images for known person")

        unknown_images = encode_faces([self.sam_will_trail])
        best_matches = match_best([test_person], unknown_images[0].encodings_in_image)
        self.assertEqual(1, len(best_matches), "couldn't match a face using multiple images for known person")

    # Should work with multiple matches in picture
    def test_multiple_unknown_in_picture(self):
        unknown_images = encode_faces([self.multiple_people])
        best_matches = match_best([self.test_person], unknown_images[0].encodings_in_image)
        self.assertEqual(1, len(best_matches), "face didn't match with itself in a picture with other people as well")

    # Shouldn't match on different person
    def test_no_match(self):
        unknown_images = encode_faces([self.different_person])
        best_matches = match_best([self.test_person], unknown_images[0].encodings_in_image)
        self.assertEqual(0, len(best_matches), "face matched against a different face")

    # Shouldn't match on a mushroom
    def test_not_a_person(self):
        unknown_images = encode_faces([self.mushroom])
        faces_found = len(unknown_images[0].encodings_in_image)
        self.assertEqual(0, faces_found, "found a face match when looking at a mushroom")
