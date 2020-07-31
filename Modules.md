# Modules
Broad breakdowns of functionality.

## KnownPerson
Represents an identified person.

Id: int - Database id of this person
Name: str
SamplePictures: List[str] - Paths of pictures of this person that encoding is based on
FaceEncoding: numpy array?

## ImageFile
Represents an image on disk that may or may not yet have been processed, or may have been processed by only _some_ algorithms and not others. Will be uniquely identified by file name and date modified, and confirmed by a hash once added to the database.

? How should this be initialized? What's the absolute minimum we can have and still have a valid image? Path?
? Which fields should we write tags to? How should they be formatted?

* Is_Tracked -> bool - Is this in the database right now?
* People: List[Person] - List of people in this image
* TechQuality: float - Technical quality of picture
* SubjectiveQuality: float - Aesthetic quality of picture
* ~~QueryDatabase -> None - Get this file's data from the database.~~ Don't do this, initiate from the DAL
* SaveTags -> bool - Write current data that should be in tags to disk.
    * This makes more sense to do from the image because the image needs to control how its tags are written
* EXIF fields: Date taken, exposure, lens, location if any
* Resolution

Needs:
* Must be able to read image data, ie the payload/contents
* Must be able to read and write IPTC data to store tags. Which fields?
* Should be able to read EXIF data
* Should be able to read date modified for a file

Solutions:
* Reading image data: handled by OpenCV and face_recognition
* Reading/writing IPTC: [iptcinfo3](https://github.com/jamesacampbell/iptcinfo3) (install from pip)
* Reading/writing EXIF: [piexif](https://pypi.org/project/piexif/) (install from pip)
* Reading/writing NTFS metadata? `os.path.getmtime(path)` gives modified time. Good enough?

## Database interactions
SQLite is [built in](https://docs.python.org/3/library/sqlite3.html) (`import sqlite3`)

* ImageFile
* KnownPerson


## To be fleshed out
* Image file manipulation (read/write images and tags)
* Face detection
* Face alignment
* Face recognition
* Database interactions
* UI Controllers
* UI (label face groups, search database)
* Person (Name, sample image path, encoded face)
* PersonStore (allows retrieving people easily by name/path/best match for encoding?)