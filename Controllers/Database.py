import sqlite3
from datetime import datetime
from typing import List, Optional
import logging
import numpy
from numpy.core.multiarray import ndarray

from pprint import pprint as pp
import os

from Model.ImageFile import ImageFile
from Model.Person import Person
from Model.FaceEncoding import FaceEncoding


class Database:
    """
    Static: All database connections
    Instance: A database connection
    By convention, operations that add items will return the id of the item created.
    """
    open_connections = []
    datetime_format_string = "%Y%m%d-%H%M"  # Should result in 20200804-0934, etc.
    logger = logging.getLogger(__name__)

    # TODO: Refactor to put metadata fields (exposure, etc.) on their own table
    # TODO: Use exif.date_taken instead of date_modified to identify files. Needs to be hhmmss instead of hhmm though.

    def __init__(self, db_file_path: str):
        self.db_file_path = db_file_path
        self.connection = sqlite3.connect(db_file_path, detect_types=sqlite3.PARSE_COLNAMES, isolation_level=None)
        self.open_connections.append(self)

        # Create tables if they don't already exist: Image, Person, PersonInImage
        self.create_schema()

        # Enables accessing results by name
        self.connection.row_factory = sqlite3.Row

    def close(self):
        self.connection.close()
        self.open_connections.remove(self)
        print(f"Successfully closed database at {self.db_file_path}")

    @classmethod
    def close_all(cls):
        for c in cls.open_connections:
            c.close()

    def create_schema(self):
        # TODO: Benchmark each index

        """
        Initializes an empty database.
        :return:
        """
        create_tables = """
        CREATE TABLE IF NOT EXISTS Image    --A single image file per row
            (id INTEGER PRIMARY KEY, 
            filename TEXT NOT NULL, 
            path TEXT NOT NULL, 
            date_modified DATETIME NOT NULL, 
            size_bytes INT NOT NULL,
            aperture REAL, shutter_speed REAL, iso INT, date_taken TEXT,
            UNIQUE(filename, date_modified, size_bytes)
            );

        CREATE TABLE IF NOT EXISTS Person   --A single individual person per row
            (id INTEGER PRIMARY KEY, name TEXT NOT NULL);

        CREATE TABLE IF NOT EXISTS Encoding --Encoded version of a face found in an image
            (id INTEGER PRIMARY KEY, 
            encoding BLOB);

        CREATE TABLE IF NOT EXISTS ImageEncoding    --A relationship between an image and an encoding
            (id INTEGER PRIMARY KEY, 
            image_id INT,
            encoding_id TEXT,
            FOREIGN KEY (image_id) REFERENCES Image (id),
            FOREIGN KEY (encoding_id) REFERENCES Encoding (id),
            UNIQUE(image_id,encoding_id)
            );
                        
        CREATE TABLE IF NOT EXISTS PersonEncoding    --A relationship between an person and an encoding
            (id INTEGER PRIMARY KEY, 
            person_id INT,
            encoding_id INT,
            FOREIGN KEY (person_id) REFERENCES Person (id),
            FOREIGN KEY (encoding_id) REFERENCES Encoding (id),
            UNIQUE(person_id,encoding_id)
            );
        
        --Going to happen a lot in bulks
        CREATE INDEX IF NOT EXISTS idx_image_in_db ON Image (filename, date_modified, size_bytes); 
                
        CREATE INDEX IF NOT EXISTS idx_encodings_from_image ON ImageEncoding (image_id); 
        """
        self.connection.executescript(create_tables)

        # DEBUG
        if False:
            all_tables = self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view','index') AND name NOT LIKE 'sqlite_%'").fetchall()
            pp(all_tables)

    def add_image(self, image: ImageFile, encodings: List[ndarray]) -> int:
        """
        Adds one image entry to the database.
        :param image: ImageFile to add
        :return: Id of the created image record
        """
        # Check for existence
        exist_check = self.get_image_id_by_attributes(image)
        if exist_check:
            return exist_check

        # Insert images
        insert_image = """
        INSERT INTO Image 
        (filename, date_modified, size_bytes, aperture, shutter_speed, iso, date_taken, path) 
        values (?, ?, ?, ?, ?, ?, ?, ?)
        --      0  1  2  3  4  5  6  7  
        """
        dbresponse = self.connection.execute(insert_image, self.adapt_ImageFile(image))
        image.dbid = dbresponse.lastrowid

        # Insert associated encodings
        for enc in encodings:
            self.add_encoding(enc, image.dbid, image=True)

        self.connection.commit()
        image.in_database = True
        return image.dbid

    def update_image_attributes(self, image: ImageFile) -> None:
        sql = """
            UPDATE Image
            SET
                date_modified = ?,
                size_bytes = ?,
                aperture = ?,
                shutter_speed = ?,
                iso = ?,
                date_taken = ?
            WHERE
                id = ?
        """
        params = self.adapt_ImageFile(image)[1:7] + [image.dbid]
        dbresponse = self.connection.execute(sql, params)
        result = dbresponse.fetchall()
        if dbresponse.rowcount != 1:
            raise Exception(f"Unexpected behavior: wrong number of rows modified: {dbresponse.rowcount}")

    def add_person(self, name) -> int:
        """
        Adds a person to the database.
        :return: The new person's id
        """

        sql = """
        INSERT INTO Person (name) VALUES (?)
        """
        dbresponse = self.connection.execute(sql, [name])
        dbid = dbresponse.lastrowid
        return dbid

    def add_encoding(self, encoding: ndarray, associate_id: int, person: bool = False, image: bool = False) -> int:
        """
        Adds an encoding to the database. They must be associated to an existing person or image.
        :param encoding: The encoding's payload
        :param associate_id: The id of the image or person this is associated with
        :param person: Is this associated to a person?
        :param image: Is this associated to an image?
        :return: Id of the newly-created encoding
        """
        # Insert
        sql = "INSERT INTO Encoding (encoding) VALUES (?)"
        encoding_bytes = encoding.tobytes()
        dbresponse = self.connection.execute(sql, [encoding_bytes])
        dbid = dbresponse.lastrowid

        self.get_or_associate_encoding(dbid, associate_id, person, image)
        return dbid

    def get_or_associate_encoding(self, encoding_id: int, associate_id: int, person: bool = False, image: bool = False):
        """
        Associate an encoding to a person or image
        :param encoding_id: The id of the encoding to associate
        :param associate_id: The id of the image or person this is associated with
        :param person: Is this associated to a person?
        :param image: Is this associated to an image?
        :return: Id of new association
        """
        # Check for pre-existing
        if person + image < 1:
            raise Exception("Must specify a person or image to associate an encoding to.")

        if person:
            sql = "SELECT id FROM PersonEncoding WHERE encoding_id = ? AND person_id = ?"
        if image:
            sql = "SELECT id FROM PersonEncoding WHERE encoding_id = ? AND person_id = ?"
        dbresponse = self.connection.execute(sql, [encoding_id, associate_id])
        result = dbresponse.fetchall()
        if len(result) == 1:
            return result[0]["id"]

        # Insert
        if person:
            sql = "INSERT INTO PersonEncoding (encoding_id, person_id) VALUES (?,?)"
        elif image:
            sql = "INSERT INTO ImageEncoding (encoding_id, image_id) VALUES (?,?)"
        else:
            raise ValueError("Must specify a type of encoding association.")
        dbresponse = self.connection.execute(sql, [encoding_id, associate_id])
        dbid = dbresponse.lastrowid
        return dbid

    def get_image_id_by_attributes(self, image: ImageFile) -> Optional[int]:
        """
        Searches the database for an image with a given filename/date-modified/filesize combination.
        :param image: The image to check the database for
        :return: Whether the image was found or not
        """
        # Get image
        sql = "SELECT * FROM Image WHERE filename = ? AND date_modified = ? AND size_bytes = ?"
        params = self.adapt_ImageFile(image, include_path=False)
        dbresponse = self.connection.execute(sql, params[0:3])  # Don't use exposure values
        result = dbresponse.fetchall()

        if len(result) > 1:
            raise Exception(f"Multiple Image records matched the file  '{image.filepath}'")
        if len(result) < 1:
            return None

        image_row = result[0]
        dbid = image_row["id"]

        return dbid

    def get_encodings_by_image_id(self, image_id: int) -> List[FaceEncoding]:
        sql = """
        SELECT E.id, E.encoding
        FROM ImageEncoding IE
        INNER JOIN Encoding E ON IE.encoding_id = E.id
        WHERE IE.image_id = ?
        """
        dbresponse = self.connection.execute(sql, [image_id])
        encoding_rows = dbresponse.fetchall()
        output = []
        for row in encoding_rows:
            encoding = numpy.frombuffer(row["encoding"], dtype="float64")
            output.append(FaceEncoding(row["id"], encoding))
        return output

    def get_encodings_by_person_id(self, person_id: int) -> List[FaceEncoding]:
        sql = """
            SELECT E.id, E.encoding
            FROM PersonEncoding PE
            INNER JOIN Encoding E ON PE.encoding_id = E.id
            WHERE PE.person_id = ?
        """
        dbresponse = self.connection.execute(sql, [person_id])
        encoding_rows = dbresponse.fetchall()
        output = []

        # TODO: Code duplication, add adapter/converter
        for row in encoding_rows:
            encoding = numpy.frombuffer(row["encoding"], dtype="float64")
            output.append(FaceEncoding(row["id"], encoding))
        return output

    def get_images_by_person_id(self, person_id: int) -> List[str]:
        sql = """
            SELECT
                I.path
            FROM PersonEncoding PE
            INNER JOIN ImageEncoding IE ON PE.encoding_id = IE.encoding_id
            INNER JOIN Image I ON IE.image_id = I.id
            WHERE PE.person_id = ?
        """
        dbresponse = self.connection.execute(sql, [person_id])
        results = dbresponse.fetchall()
        return [row["path"] for row in results]

    def get_all_people(self):
        sql = "SELECT * from Person"
        dbresponse = self.connection.execute(sql)
        results = dbresponse.fetchall()

        output = []
        for p_row in results:
            person_id = p_row["id"]
            found_encodings = self.get_encodings_by_person_id(person_id)
            output.append(Person(person_id, p_row["name"], found_encodings))

        return output

    def get_person_by_name(self, name: str) -> Optional[Person]:
        sql = "SELECT * FROM Person WHERE name = ?"
        dbresponse = self.connection.execute(sql, [name])
        results = dbresponse.fetchall()

        if len(results) < 1:
            return None
        if len(results) > 1:
            raise Exception(f"Multiple people found with name {name}")
        row = results[0]
        person_id = row["id"]
        encodings = self.get_encodings_by_person_id(person_id)

        return Person(person_id, row["name"], encodings)

    # Pseudo-adapters - Don't always want every parameter, so not using the real "adapters" functionality
    @classmethod
    def adapt_ImageFile(cls, image: ImageFile, include_path: bool = True):
        # Date and time stamp of the last time the file was modified
        mtime = cls.get_formatted_date_modified(image.filepath)

        exif_data = image.get_salient_exif_data()
        date_taken = exif_data.get("date_taken")
        date_taken = date_taken and date_taken.strftime(cls.datetime_format_string)  # Null conditional

        # Relative path is last because we won't always use it
        output = [os.path.basename(image.filepath),  # 0
                  mtime,                             # 1
                  os.path.getsize(image.filepath),   # 2
                  exif_data.get("aperture"),         # 3
                  exif_data.get("shutter_speed"),    # 4
                  exif_data.get("iso"),              # 5
                  date_taken                         # 6
                  ]
        if include_path:
            output.append(image.filepath)            # 7

        return output

    @classmethod
    def get_formatted_date_modified(cls, filepath: str):
        return datetime.fromtimestamp(os.path.getmtime(filepath)).strftime(cls.datetime_format_string)
