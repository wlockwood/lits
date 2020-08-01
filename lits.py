__help_text__ = """
Main execution module for LITS - Local Image Tagging and Search.
Exmaple usage:
`py lits.py -scanroot c:\pictures -known c:\pictures\lits-people [-db cache.db -tolerance 0.5]`
Required:
-scanroot is the root of the pictures to be scanned for faces.
-known is the root of the folder structure where identified people can be found.
Optional:
-db is the path to e SQLite database. Will be loaded if exists and created if not.
-tolerance is optional and adjusts how strict face matches should be to be considered a match.
    Defaults to 0.6, lower numbers are stricter and will reduce false positives at the cost
    of increasing false negatives.

Author: William Lockwood
GitHub: wlockwood/lits
"""

# Builtins
import argparse
from os import path, getcwd, listdir
from typing import List

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
    parser.add_argument("--help")
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
    db = Database(args.db)


    # Initialize list of known people
    # TODO: Check with the database and merge with/filter filesystem results
    # TODO: Add support for people folders instead of just single pictures
    # TODO: Filter for supported file types.
    known_person_images = [Image(path.join(args.known, f)) for f in listdir(args.known)
                           if path.isfile(path.join(args.known, f))]
    encode_faces(known_person_images, jitter=3)
    known_people: List[Person] = []
    for im in known_person_images:
        # TODO: This assumes all files have an extension, which is fragile.
        name = path.basename(im.path).split(".")[0:-1]

    # Build list of files to scan
    images_to_scan = [Image(path.join(args.known, f)) for f in listdir(args.known)
                      if path.isfile(path.join(args.known, f))]


    # Encode faces in files to scan (expensive!)
    # TODO: Multiprocess here on a per-image basis
    # TODO: Add support for GPU encoding
        # Encode

        # Save to image (saving to image first means that a concurrency crash is faster to recover from)

        # Save to database


    # Once all faces are encoded, scan through each picture and compare with all known faces
    # TODO: After speeding up the encoding step (previous) this should be in the second pass of optimization
        # Find best match

        # Save found person's/people's names to image

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