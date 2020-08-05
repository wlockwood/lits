from typing import List, Any
from collections import namedtuple

import numpy
from numpy.core.multiarray import ndarray  # Encoded faces

from Model.Person import Person
from Model.ImageFile import ImageFile
import face_recognition as fr
from PIL import Image as pilmage
from os import path

import unittest

GOAL_SIZE = 1250  # Determined by testing as a good compromise between speed and accuracy


def encode_faces(filepath: str, jitter: int = 1, resize_to: int = 1500) -> List[ndarray]:
    """
    Populates the encodings_in_image field of an Image

    :param image: An ImageFile with zero or more faces in it.
    :param jitter: How many times to transform a face. Higher number is slower but more accurate.
    :param resize_to: Size to resize to. Lower number is faster but less accurate.
    :return: The input list of images.
    """
    # TODO: EXIF rotate images prior to encoding them

    content = pilmage.open(filepath)

    # Resize image to around 1k pixels

    scale_factor = GOAL_SIZE / max(content.size[0], content.size[1])
    new_x, new_y = int(round(content.size[0] * scale_factor)), \
                   int(round(content.size[1] * scale_factor))
    resized = content.resize((new_x, new_y))
    as_numpy_arr = numpy.array(resized)

    found_encodings = fr.face_encodings(as_numpy_arr, num_jitters=jitter, model="large")
    return found_encodings


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
