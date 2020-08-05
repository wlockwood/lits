# LITS: Local Image Tagging and Search
Locally-run neural-network tagging for images. To eventually include faces, emotion, quality, and more.

LITS generates encoded versions of known people and will scan all pictures found in a specified folder, apply face recognition to all supported file formats and keep track of which people are in which images by writing known, found people to the metadata tags of a picture. This allows those pictures to be searched from photography library management tools such as Photoshop Lightroom. 

Initially, LITS will only _tag_ images to enable search elsewhere, but future versions will supply a facility for querying the internal database.

**JPEG** is the only fully supported file type as other types either lack appropriate metadata fields or have different fields.

**Untested** but probably functional file formats: .png, .bmp, .gif and other simple raster image formats should work, but their lack of JPEG-like metadata fields limits the utility of doing so. Future versions may support more metadata types than IPTC. By default, LITS will filter these out, but the user can modify the `valid_extensions` variable in `lits.py` if they want to test out a specific file type.  

**Untested** and unlikely-to-be functional formats: [everything Pillow can read](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html).  By default, LITS will filter these out, but the user can modify the `valid_extensions` variable in `lits.py` if they want to test out a specific file type.  

**Unsupported** file formats: DNG and other raw files. Anything that's not a picture.

# Usage
After installation, run LITS from a command line in the following fashion:  
`py lits.py -scanroot c:\pictures -known c:\pictures\lits-people [-db cache.db -tolerance 0.5]`

Future versions may include a graphical interface.

## `-scanroot` / Images to scan
`-scanroot` specifies the root of the folder structure where pictures are to be scanned for matches to the known people and, later, other features. 

Not yet implemented: If the scan root path includes the known image root, the known image root and all its subfolders will be ignored.

## `-known` / Known Image Root
`-known` specifies the root of the folder structure where identified people can be found. Inside should be any combination of:
* single pictures labeled with a name, such was `William Lockwood.jpg`
* folders labeled with a name, such as `William Lockwood`, under which one or more pictures for that person can be found. File names inside this named folder don't need to follow any special logic.

## `-db` / Database
`-db` specifies where the SQLite database will be stored. Defaults to be `lits.db` in the unknown image root.

In addition to writing directly to each image's metadata, LITS will build a database with much of this information in it so that it can quickly identify which files it's already encoded and not need to reprocess them. This significantly decreases the time it takes to update the tagging data when doing a delta after adding more pictures to the collection.

Future versions will enable the user to search the database directly.

## `-tolerance` / Face Matching Tolerance
`-tolerance` is optional and adjusts how strict face matches should be to be considered a match. 
This defaults to 0.6, and lower inputs (ex: 0.2) force stricter matches at the cost of more false negatives

# Install Manual 

Development environment is Windows, so installation assumes that. Installing in other environments should be doable with slight modifications that are left as an exercise to the Linux-using reader.

## Windows Install
1. Install Python3 from https://www.python.org/downloads/.
   - This should already come with pip and virtualenv.
1. Create a virtual environment for your LITS install: `py -m venv env`
1. Install face_recognition: `pip install face_recognition`.
1. Install pyexiv2: `pip install pyexiv2`
1. Download SQLite tools if you want to run queries against the database that is built. This may be integrated in future versions.
