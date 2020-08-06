__help_text__ = """
Main execution module for LITS - Local Image Tagging and Search.
Exmaple usage:
`py lits.py --scanroot c:\pictures --known c:\pictures\lits-people [-db cache.db -tolerance 0.5]`
Required:
--scanroot is the root of the pictures to be scanned for faces.
--known is the root of the folder structure where identified people can be found.
Optional:
--db is the path to e SQLite database. Will be loaded if exists and created if not.
--tolerance is optional and adjusts how strict face matches should be to be considered a match.
    Defaults to 0.6, lower numbers are stricter and will reduce false positives at the cost
    of increasing false negatives.

Author: William Lockwood
GitHub: wlockwood/lits
"""

# Builtins
import argparse
from os import path, getcwd
from glob import glob
from typing import List, Optional, Dict
from time import perf_counter as pc
from datetime import datetime
import logging
# External modules

# Custom modules
from numpy.core.multiarray import ndarray

from Model.FaceEncoding import FaceEncoding
from Model.Person import Person
from Model.ImageFile import ImageFile
from Controllers.Database import Database
from Controllers.FaceRecognizer import encode_faces, match_best

valid_extensions = [".jpg"]  #[".jpg", ".png", ".bmp", ".gif"]
log_path = "lastrun.log"
logger = logging.getLogger(__name__)

def main():
    print("LITS initializing...")
    print(f"Running from {getcwd()}, logging to {log_path}")
    logging.basicConfig(filename=log_path, level=logging.DEBUG)

    # Parse arguments and check validity
    parser = argparse.ArgumentParser()
    parser.add_argument("--scanroot", help="Directory to look for taggable images", required=True)
    parser.add_argument("--known", help="Directory of known people's faces", required=True)
    parser.add_argument("--db", help="Path to the database file or where to create it", default="lits.db")
    parser.add_argument("--tolerance", help="Lower forces stricter matches", default=0.6, type=float)
    # TODO: Add "--clear-keywords"? Would ignore pre-existing keywords when applying new
    # TODO: Add "--rescan"? Would ignore encodings cached in database
    args = parser.parse_args()

    assert path.exists(args.scanroot), f"'scanroot' path doesn't exist: {path.abspath(args.scanroot)}"
    assert path.exists(args.known), f"'known' path doesn't exist: {path.abspath(args.known)}"
    if path.exists(args.db):
        print(f"Found pre-existing database at {path.abspath(args.db)}")
    else:
        print(f"Will create new database at {path.abspath(args.db)}")


    # Initialize database
    db = Database(args.db)

    # Initialize list of known people
    # TODO: Add support for people folders instead of just single pictures
    known_person_images = get_all_compatible_files(args.known)
    print(f"{len(known_person_images):,} images of known people in {args.known}")

    for kpi in known_person_images:
        # Ensure image is already in database
        image_id = ensure_image_in_database(db, kpi)

        # Make sure it's a picture of just one person
        encodings_in_image = db.get_encodings_by_image_id(image_id)
        if len(encodings_in_image) != 1:
            raise Exception(f"Image {kpi.filepath} can't be a known person image as no faces or multiple were found.")

        kpi_encoding: FaceEncoding = db.get_encodings_by_image_id(image_id)[0]

        # Ensure this image's encoding is associated to the person named in its filename
        person_name: str = just_filename(kpi.filepath)
        found_person = db.get_person_by_name(person_name)

        if not found_person:  # If person doesn't exist, create them and associate their first face encoding
            person_id = db.add_person(person_name)
            encoding_id = db.get_or_associate_encoding(kpi_encoding.dbid, associate_id=person_id, person=True)
        else:  # Person already exists, associate this encoding if it's not already so
            matching_encodings = [enc for enc in found_person.encodings if enc.equals(kpi_encoding)]

            if len(matching_encodings) > 0:
                logging.debug(f"File {kpi.filepath} already in database for person '{person_name}'.")

            if len(matching_encodings) == 0:  # No match, so associate this encoding to person
                db.get_or_associate_encoding(kpi_encoding.dbid, associate_id=found_person.dbid, person=True)
                logging.debug(
                    f"File {kpi.filepath} already in database, but wasn't associated with person '{person_name}'.")

    # Database now up to date, extract all known people
    known_people = db.get_all_people()
    print(f"{len(known_people):,} known people found in database.")

    # Build list of files to scan
    images_to_scan = get_all_compatible_files(args.scanroot)
    print(f"{len(images_to_scan):,} images in scanroot")

    # Remove images that are in the known folder, if any
    images_to_scan = [im for im in images_to_scan if path.abspath(im.filepath)
                      not in [path.abspath(kpi.filepath) for kpi in known_person_images]]
    print(f"{len(images_to_scan):,} images to scan after removing known-person images")

    # Encoding images - the bulk of the work
    # Prep statistics for encoding
    total = len(images_to_scan)
    scan_count = 0
    timers = []
    start_time = pc()
    # Encode faces in files to scan (expensive!)
    print(f"{len(images_to_scan):,} unscanned images")
    print(f"Starting scan at {datetime.now()}")

    for image in images_to_scan:  # Iterating individually for now to make progress reporting easier
        # UI Updates
        progress_percent = f"{scan_count / total * 100:3.1f}%"
        matched_people_list = ", ".join(mp.name for mp in image.matched_people)
        print(f"{progress_percent}\tProcessing '{image.filepath}'...")

        image_start_time = pc()

        # TODO: Parallelize here on a per-image basis
        # TODO: Add error handling so single-image problems won't crash the whole run.
        image_id = ensure_image_in_database(db, image)
        image.encodings_in_image = db.get_encodings_by_image_id(image_id)

        # Match people
        if len(image.encodings_in_image) > 0:
            found_people: Dict[Person, FaceEncoding] = match_best(known_people, image.encodings_in_image)

            # Write to file *prior* to storing to DB, else all the date_modified values would never match
            image.matched_people = found_people.keys()
            if len(image.matched_people) > 0:
                image.append_keywords([mp.name for mp in image.matched_people])

            # Store to database
            for person, enc in found_people.items():
                db.get_or_associate_encoding(enc.dbid, associate_id=person.dbid, person=True)

        # Stats and UI updates
        scan_count += 1

        time_taken = pc() - image_start_time
        timers.append(time_taken)

    print(f"Done encoding {total:,} images. ({pc() - start_time:.0f}s total)")
    print(f"Image times: {sum(timers):,.1f}s, avg {sum(timers) / len(timers):.2}s, max {max(timers):.2}")

    # Report statistics
    """
    Images scanned
    Found faces
    Time taken
    Image scan rate
    Faces found per image
    Most-common person found
    """


def ensure_image_in_database(db: Database, image: ImageFile) -> int:
    image_id = db.get_image_id_by_attributes(image)
    if image_id:
        encodings: List[FaceEncoding] = db.get_encodings_by_image_id(image_id)
        logging.debug(f"File {image.filepath} already in database (image_id: {image_id}) with {len(encodings)} faces(s).")
    else:  # Encode and save
        new_encodings: List[ndarray] = encode_faces(image.filepath)
        image_id = db.add_image(image, new_encodings)
        logging.debug(f"File {image.filepath} added to database (image_id: {image_id}) with {len(new_encodings)} face(s).")
    return image_id


def validate_path_exists(check_path: str, name: str):
    if path.exists(check_path):
        print(f"'{name}' will be '{path.abspath(check_path)}'.")
    else:
        soft_exit(f"'{name}' path doesn't exist or is inaccessible. Evaluated to:\n\t{path.abspath(check_path)}")

def get_all_compatible_files(folderpath: str) -> List[ImageFile]:
    all_matching: List[str] = []
    extensions = ["*" + ext for ext in valid_extensions]
    for extension in extensions:
        all_matching.extend(glob(folderpath + "/**/" + extension, recursive=True))
    wrapped = [ImageFile(file) for file in all_matching]
    return wrapped

def just_filename(in_path: str):
    return path.splitext(path.basename(in_path))[0]

def soft_exit(message: str = ""):
    if message:
        print(message)
    Database.close_all()
    print("Exiting...")
    exit()


if __name__ == "__main__":
    main()
    soft_exit("LITS Done!")
