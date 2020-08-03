# Builtins
import unittest
import uuid
from os import path
from pprint import pprint as pp

# Custom modules
from Controllers.FaceRecognizer import encode_faces, match_best
from Model.Image import Image
from Model.Person import Person


class TestFaceRecognizer(unittest.TestCase):
    my_dir = path.dirname(__file__)
    test_data_path = "test-data\\"

    known_images = [Image(test_data_path + "known\\will.jpg", skip_md_init=True)]
    test_faces = encode_faces(known_images)
    test_person = Person("will")
    test_person.encodings = test_faces[0].encodings_in_image

    will_as_unknown = Image(test_data_path + "unknown\\will2.jpg", skip_md_init=True)
    sam_will_trail = Image(test_data_path + "unknown\\sam will trail 2.jpg", skip_md_init=True)
    mushroom = Image(test_data_path + "unknown\\mushroom.jpg", skip_md_init=True)
    multiple_people = Image(test_data_path + "unknown\\work group will.jpg", skip_md_init=True)
    different_person = Image(test_data_path + "unknown\\jackie phone.jpg", skip_md_init=True)

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
        test_person = Person("will")
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


class TestImage(unittest.TestCase):
    test_image = Image(r"test-image.jpg")

    # Tests unused code now
    @unittest.skip("Not yet working")
    def test_encoding_rw_cycle(self):
        test_encoding = encode_faces([self.test_image])[0].encodings_in_image[0]
        self.test_image.init_metadata()
        print("Pre-write XMP data")
        pp(self.test_image.xmp)

        self.test_image.set_encodings_in_metadata(self.test_encoding)

        self.test_image.init_metadata()
        print("Post-write XMP data")
        pp(self.test_image.xmp)
        readout = self.test_image.get_encodings_from_metadata()
        all_match = True
        for i in range(len(self.test_encoding)):
            if self.test_encoding[i] != readout[i]:
                all_match = False
                break
        self.assertEqual(True, all_match, "test array doesn't match itself after having been written to and from file")

    def setUp(self):
        self.test_image.clear_keywords()

    def test_clear_keywords(self):
        self.test_image.append_keywords(["TESTING keyword clearing"])
        self.test_image.clear_keywords()
        self.assertEqual(0, len(self.test_image.get_keywords()), "keywords should be blank, but aren't")

    def test_append_single(self):
        rand_keyword = str(uuid.uuid4())  # In case the clear fails, guid should prevent tests passing falsely
        self.test_image.append_keywords([rand_keyword])
        readout = self.test_image.get_keywords()
        self.assertEqual(1, len(readout), "Appending a single keyword resulted in multiple keywords written")
        self.assertEqual(rand_keyword, readout[0])

    def test_append_multiple(self):
        rand_keywords = [str(uuid.uuid4()) for i in range(3)]
        self.test_image.append_keywords(rand_keywords)
        readout = self.test_image.get_keywords()
        self.assertEqual(len(rand_keywords), len(readout))
        self.assertListEqual(rand_keywords, readout)

    def test_append_duplicate(self):
        rand_keyword = str(uuid.uuid4())
        self.test_image.append_keywords([rand_keyword])
        self.test_image.append_keywords([rand_keyword])
        self.test_image.append_keywords([rand_keyword])
        readout = self.test_image.get_keywords()
        self.assertEqual(1, len(readout),"Adding the same keyword multiple times wasn't de-duplicated.")
