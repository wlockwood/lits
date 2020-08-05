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
from os import path, getcwd, listdir
from typing import List
from time import perf_counter as pc
from datetime import datetime
# External modules

# Custom modules
from Model.Person import Person
from Model.ImageFile import ImageFile
from Controllers.Database import Database
from Controllers.FaceRecognizer import encode_faces, match_best

valid_extensions = [".jpg", ".png", ".bmp", ".gif"]


def main():
    print("LITS initializing...")
    print(f"Running from {getcwd()}")

    # Parse arguments and check validity
    parser = argparse.ArgumentParser()
    parser.add_argument("--scanroot", help="Directory to look for taggable images", required=True)
    parser.add_argument("--known", help="Directory of known people's faces", required=True)
    parser.add_argument("--db", help="Path to the database file or where to create it", default="lits.db")
    parser.add_argument("--tolerance", help="Lower forces stricter matches", default=0.6, type=float)
    # TODO: Add "--clear-keywords"? Would ignore pre-existing keywords when applying new
    # TODO: Add "--rescan"? Would ignore encodings cached in database
    args = parser.parse_args()

    validate_path_exists(args.scanroot, "scanroot")
    validate_path_exists(args.known, "known")
    validate_path_exists(args.db, "db")

    # Initialize database
    db = Database(args.db)

    # Initialize list of known people
    # TODO: Add support for people folders instead of just single pictures
    # TODO: Filter for supported file types.
    known_person_images = get_all_compatible_files(args.known)
    print(f"{len(known_person_images):,} images of known people")

    get_or_compute_encodings(db, known_person_images, jitter=3)
    known_people: List[Person] = []
    for im in known_person_images:
        name, extension = path.splitext(im.filepath)
        new_person = Person(name)
        new_person.encodings = im.encodings_in_image
        known_people.append(new_person)


    # Build list of files to scan
    images_to_scan = get_all_compatible_files(args.scanroot)
    print(f"{len(images_to_scan):,} images in scanroot")

    # Remove images that are in the known folder
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
        image_start_time = pc()
        # TODO: Parallelize here on a per-image basis
        get_or_compute_encodings(db, [image])

        # Match people
        if len(image.encodings_in_image) > 0:
            found_people = match_best(known_people, image.encodings_in_image)
            image.matched_people = found_people
            if len(image.matched_people) > 0:
                image.append_keywords([mp.name for mp in image.matched_people])

        # Save to database
        # TODO: Write to database

        # Stats and UI updates
        scan_count += 1
        progress_percent = f"{scan_count / total * 100:3.1f}%"
        time_taken = pc() - image_start_time
        matched_people_list = ", ".join(mp.name for mp in image.matched_people)
        print(progress_percent, f" Found {len(image.encodings_in_image)} faces in '{image.filepath}':",
              f"{matched_people_list} ({time_taken:.1f}s)")
    print(f"Done encoding {total:,} images. ({pc() - start_time:.0f}s total)")

    # Report statistics
    """
    Images scanned
    Found faces
    Time taken
    Image scan rate
    Faces found per image
    Most-common person found
    """


def validate_path_exists(check_path: str, name: str):
    if path.exists(check_path):
        print(f"'{name}' will be '{path.abspath(check_path)}'.")
    else:
        soft_exit(f"'{name}' path doesn't exist or is inaccessible. Evaluated to:\n\t{path.abspath(check_path)}")


def get_all_compatible_files(folderpath: str):
    all_files = [path.join(folderpath, file) for file in listdir(folderpath)
                 if path.isfile(path.join(folderpath, file))

                 ]
    valid_files = [f for f in all_files if path.splitext(f)[1] in valid_extensions]
    as_images = [ImageFile(f) for f in all_files]
    return as_images


def check_images_against_database(database: Database, images: List[ImageFile]):
    for image in images:
        database.get_image_data_by_attributes(image)

def get_or_compute_encodings(database: Database, images: List[ImageFile], jitter = None) -> None:
    """
    Check database and populate any existing encodings. Run face_recognition's encoder (expensive!) otherwise.
    ImageFiles will be updated in place.
    :param database:
    :param images:
    """
    for image in images:
        db_check = database.get_image_data_by_attributes(image)
        if db_check is None:

            if jitter:
                encode_faces([image], jitter)
            else:
                encode_faces([image])
            database.add_image(image)
            print(f"Encoded {image.filepath} and added to database with image id {image.dbid}")
        else:
            print(f"Found {image.filepath} in database with image id {image.dbid}")

def soft_exit(message: str = ""):
    if message:
        print(message)
    Database.close_all()
    print("Exiting...")
    exit()


if __name__ == "__main__":
    main()
    soft_exit("LITS Done!")
