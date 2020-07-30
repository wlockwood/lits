from typing import List, Any


class FaceRecognizer:
    def __init__(self, known_faces_path: str, unknown_faces_path: str, tolerance=-1):
        self.known_faces_path = known_faces_path
        self.unknown_faces_path = unknown_faces_path
        self.tolerance = tolerance

    @staticmethod
    def EncodeFaces(images: List[str], jitter: int = 1, resize_to = 750, face_locations: List = Any):
        """

        :param images: A list of image
        :param jitter: How many times to transform a face. Higher number is slower but more accurate.
        :param resize_to: Size to resize to. Lower number is faster but less accurate.
        :param face_locations:
        :return:
        """
        pass


    # https://github.com/ageitgey/face_recognition/blob/master/examples/find_faces_in_batches.py
    @staticmethod
    def FindFaces(images: List[str]):
        """

        :param images:
        :return:
        """


class Image:
    def __init__(self, path):
        self.path = path
        self.found_people: List[Person] = []

