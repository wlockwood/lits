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
from typing import List, Any
from time import perf_counter as pc
from datetime import datetime
# External modules


# Custom modules
from Model.Person import Person
from Model.Image import Image
from Controllers.Database import Database
from Controllers.FaceRecognizer import encode_faces, match_best


def main():
    print("LITS initializing...")
    print(f"Running from {getcwd()}")

    # Parse arguments and check validity
    parser = argparse.ArgumentParser()
    parser.add_argument("--scanroot", help="Directory to look for taggable images", required=True)
    parser.add_argument("--known", help="Directory of known people's faces", required=True)
    parser.add_argument("--db", help="Path to the database file or where to create it", default="lits.db")
    parser.add_argument("--tolerance", help="Lower forces stricter matches", default=0.6, type=float)
    args = parser.parse_args()

    def validate_path_exists(check_path: str, name: str):
        if path.exists(check_path):
            print(f"'{name}' will be '{path.abspath(check_path)}'.")
        else:
            soft_exit(f"'{name}' path doesn't exist or is inaccessible. Evaluated to:\n\t{path.abspath(check_path)}")


    validate_path_exists(args.scanroot, "scanroot")
    validate_path_exists(args.known, "known")
    if not (path.isdir(args.scanroot) and path.isdir(args.known)):
        print()
    validate_path_exists(args.scanroot, "db")

    # Initialize database
    db = Database(args.db)  # TODO: And then initialize


    # Initialize list of known people
    # TODO: Check with the database and merge with/filter filesystem results
    # TODO: Add support for people folders instead of just single pictures
    # TODO: Filter for supported file types.
    known_person_images = [Image(path.join(args.known, f)) for f in listdir(args.known)
                           if path.isfile(path.join(args.known, f))]
    print(f"{len(known_person_images):,} images of known people")
    encode_faces(known_person_images, jitter=3)
    known_people: List[Person] = []
    for im in known_person_images:
        # TODO: This assumes all files have an extension, which is fragile.
        name = path.basename(im.path).split(".")[0:-1]
        new_person = Person(name)
        new_person.encodings = im.encodings_in_image
        known_people.append(new_person)

    print(f"{len(known_people):,} images of known people")


    # Build list of files to scan
    images_to_scan = [Image(path.join(args.scanroot, f)) for f in listdir(args.scanroot)
                      if path.isfile(path.join(args.scanroot, f))]
    print(f"{len(images_to_scan):,} images in scanroot")

    # Remove images that are in the known folder
    images_to_scan = [im for im in images_to_scan if path.abspath(im.path)
                      not in [path.abspath(kpi.path) for kpi in known_person_images]]
    print(f"{len(images_to_scan):,} images to scan after removing known-person images")

    # Read metadata to see if encoding was already done.
    #TODO: Add override to skip this step
    Image.disable_iptc_errors()
    already_scanned: List[Image] = []
    for image in images_to_scan:
        image.init_iptc()
        existing_encs = image.get_encodings_from_metadata()
        if existing_encs and len(existing_encs) > 0:
            image.encodings_in_image = existing_encs
            already_scanned.append(image)
            images_to_scan.remove(image)
    print(f"{len(already_scanned):,} images already have face encodings and will be skipped.")

    # Prep statistics for encoding
    total = len(images_to_scan)
    scan_count = 0
    timers = []
    start_time = pc()

    # Encode faces in files to scan (expensive!)
    print(f"{len(images_to_scan):,} unscanned images")
    print(f"Starting scan at {datetime.now()}")
    for image in images_to_scan: # Iterating individually for now to make progress reporting easier
        image_start_time = pc()
        # TODO: Parallelize here on a per-image basis and/or add support for GPU encoding
        encode_faces([image])

        # Save to image (saving to image first means that a concurrency crash is faster to recover from)
        image.set_encoding_in_metadata(image.encodings_in_image)
        if image.matched_people != Any:
            for kp in image.matched_people:
                image.append_keyword(kp.name)
        image.save_iptc()

        # Save to database
        #TODO: Write to database

        # Stats and UI updates
        scan_count += 1
        progress_percent = f"{scan_count/total*100:3.1f}%"
        time_taken = pc() - image_start_time
        matched_people_list = ", ".join([mp.name for mp in image.matched_people])
        print(progress_percent, f" Found {len(image.encodings_in_image)} faces in '{image.path}':",
              f"{matched_people_list} ({time_taken:.1f}s)")
    print(f"Done encoding {total:,} images. ({pc() - start_time:.0f}s total)")

    # Once all faces are encoded, scan through each picture and compare with all known faces
    # TODO: Parallelize in batches (Second-pass optimization)
    images_to_search = already_scanned + images_to_scan
    for image in images_to_search:
        found_people = match_best(known_people, image.encodings_in_image)

        # Save found person's/people's names to image
        image.matched_people = found_people
        for p in image.matched_people:
            image.append_keyword(p.name)
        image.save_iptc()

        # Save relationships to database

    # Report statistics
    """
    Images scanned
    Found faces
    Time taken
    Image scan rate
    Faces found per image
    Most-common person found
    """

def soft_exit(message: str = ""):
    if message:
        print(message)
    Database.close_all()
    print("Exiting...")
    exit()

if __name__ == "__main__":
    main()