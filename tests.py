# Builtins
import os
import unittest
import uuid
from copy import deepcopy
from os import path
import numpy
from datetime import datetime
# Custom modules


from Controllers.Database import Database
from Controllers.FaceRecognizer import encode_faces, match_best
from Model.FaceEncoding import FaceEncoding
from Model.ImageFile import ImageFile
from Model.Person import Person

test_data_path = "unittest-images\\"
class TestFaceRecognizer(unittest.TestCase):
    my_dir = path.dirname(__file__)


    known_image = ImageFile(test_data_path + "known.jpg", skip_md_init=True)
    test_face = FaceEncoding(-1, encode_faces(known_image.filepath)[0])
    test_person = Person(-1, "will", [test_face])

    will_as_unknown = ImageFile(test_data_path + "man.jpg", skip_md_init=True)
    mushroom = ImageFile(test_data_path + "mushroom.jpg", skip_md_init=True)
    multiple_people = ImageFile(test_data_path + "people.jpg", skip_md_init=True)
    different_person = ImageFile(test_data_path + "woman right.jpg", skip_md_init=True)

    # Should match when same person
    def test_one_to_one_match(self):
        self.will_as_unknown.encodings_in_image = [FaceEncoding(-1, fe) for fe in encode_faces(self.will_as_unknown.filepath)]
        best_matches = match_best([self.test_person], self.will_as_unknown.encodings_in_image)
        self.assertEqual(len(best_matches), 1, "face didn't match itself in another picture")

    @unittest.skip("Not yet implemented")
    def test_multiple_pictures_per_known(self):
        # Requires more convoluted test setup for the known person
        known_images = []
        encode_faces(known_images)
        test_person = Person("will")
        test_person.encodings = [enc for im in known_images for enc in im.encodings_in_image]  # Flat?

        unknown_images = encode_faces(self.will_as_unknown.filepath)
        best_matches = match_best([test_person], unknown_images[0].encodings_in_image)
        self.assertEqual(1, len(best_matches), "couldn't match a face using multiple images for known person")

        unknown_images = encode_faces(self.sam_will_trail.filepath)
        best_matches = match_best([test_person], unknown_images[0].encodings_in_image)
        self.assertEqual(1, len(best_matches), "couldn't match a face using multiple images for known person")

    # Should work with multiple matches in picture
    def test_multiple_unknown_in_picture(self):
        unknown_faces = [FaceEncoding(-1, fe) for fe in encode_faces(self.multiple_people.filepath)]
        best_matches = match_best([self.test_person], unknown_faces)
        self.assertEqual(1, len(best_matches), "face didn't match with itself in a picture with other people as well")

    # Shouldn't match on different person
    def test_no_match(self):
        unknown_faces = [FaceEncoding(-1, fe) for fe in encode_faces(self.different_person.filepath)]
        best_matches = match_best([self.test_person], unknown_faces)
        self.assertEqual(0, len(best_matches), "face matched against a different face")

    # Shouldn't match on a mushroom
    def test_not_a_person(self):
        unknown_faces = [FaceEncoding(-1, fe) for fe in encode_faces(self.mushroom.filepath)]
        faces_found = len(unknown_faces)
        self.assertEqual(0, faces_found, "found a face match when looking at a mushroom")


class TestImage(unittest.TestCase):
    test_image = ImageFile(test_data_path + "known.jpg")

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
        self.assertEqual(1, len(readout), "Adding the same keyword multiple times wasn't de-duplicated.")

    def test_exif_extract(self):
        exif_data = self.test_image.get_salient_exif_data()
        self.assertEqual(1.8, exif_data["aperture"])
        self.assertEqual(1/200, exif_data["shutter_speed"])
        self.assertEqual(100, exif_data["iso"])
        self.assertEqual(datetime.strptime("2020:07:23 07:47:08", ImageFile.exif_timestamp_format), exif_data["date_taken"])



class TestDatabase(unittest.TestCase):
    # DB Info
    test_db_path = "test.db"

    # Set up a basic image to test with
    test_image_path = test_data_path + "known.jpg"
    test_image = ImageFile(test_image_path)
    base_test_image = ImageFile(test_image_path)  # Will be copied, since many DB calls are writing to the input image
    base_test_image.encodings_in_image = [FaceEncoding(-1, enc) for enc in  encode_faces(base_test_image.filepath)]

    test_person = Person(-1, "Will", base_test_image.encodings_in_image)

    base_test_image.matched_people = [test_person]
    test_person.encodings = [base_test_image.encodings_in_image[0]]

    def setUp(self):
        self.test_db = Database(self.test_db_path)

        # Clean out the database
        self.test_db.connection.executescript("DELETE FROM Image")
        self.test_db.connection.executescript("DELETE FROM Person")
        self.test_db.connection.executescript("DELETE FROM Encoding")
        self.test_db.connection.executescript("DELETE FROM PersonEncoding")
        self.test_db.connection.executescript("DELETE FROM ImageEncoding")

        # Clone the test image to reduce time spent encoding
        self.this_test_image: ImageFile = deepcopy(self.base_test_image)

    def test_add_image(self):
        # This will fail if anything else does, which isn't ideal, but I want to make sure it's thorough
        new_image_id = self.test_db.add_image(self.this_test_image, [])
        dbresponse = self.test_db.connection.execute("SELECT * FROM Image")
        result = dbresponse.fetchall()
        test_row = result[0]

        self.assertEqual(1, len(result), "Wrong number of images inserted when trying to add one")
        second_image_id = self.test_db.add_image(self.this_test_image, [])
        self.assertEqual(new_image_id, second_image_id, "Inserted same file twice, got different Ids")
        self.assertEqual(os.path.getsize(self.this_test_image.filepath), test_row["size_bytes"])

    def test_encoding_ops(self):
        self.test_db.connection.executescript("DELETE FROM Encoding")
        self.assertRaises(Exception,
                          self.test_db.add_encoding,
                          [self.this_test_image.encodings_in_image],
                          msg="Expected a failure while trying to add an unassociated encoding, but succeeded.")

        # Strip and store an encoding
        test_encoding = self.this_test_image.encodings_in_image[0].encoding
        self.this_test_image.encodings_in_image = []
        id_of_partial_image = self.test_db.add_image(self.this_test_image, [test_encoding])
        self.test_db.connection.commit()
        new_enc = self.test_db.add_encoding(test_encoding,
                                            associate_id=id_of_partial_image,
                                            image=True)

        dbresponse = self.test_db.connection.execute("SELECT * FROM Encoding")
        result = dbresponse.fetchall()

        retrieved_encoding_bytes = result[0]["encoding"]
        retrieved_encoding: numpy.ndarray = numpy.frombuffer(retrieved_encoding_bytes, "float64")

        self.assertTrue(numpy.array_equal(test_encoding, retrieved_encoding),
                        "Encoding didn't survive being stored and retrieved")
