import sqlite3
import time
from datetime import datetime
from typing import List, Optional

import numpy
from numpy.core.multiarray import ndarray

from Model.ImageFile import ImageFile
from pprint import pprint as pp
import os

from Model.Person import Person


class Database:
    """
    Static: All database connections
    Instance: A database connection
    By convention, operations that add items will return the id of the item created.
    """
    open_connections = []
    datetime_format_string = "%Y%m%d-%H%M"  # Should result in 20200804-0934, etc.

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
            (id INTEGER PRIMARY KEY, filename TEXT, path TEXT, date_modified DATETIME, size_bytes INT,
            UNIQUE(filename, date_modified, size_bytes)
            );

        CREATE TABLE IF NOT EXISTS Person   --A single individual person per row
            (id INTEGER PRIMARY KEY, name TEXT);

        CREATE TABLE IF NOT EXISTS ImagePerson  --A relationship between an image and a person
            (id INTEGER PRIMARY KEY, 
            image_id INT,
            person_id INT,
            FOREIGN KEY (image_id) REFERENCES Image (id), 
            FOREIGN KEY (person_id) REFERENCES Person (id)
            );
         

        CREATE TABLE IF NOT EXISTS Encoding --Encoded version of a face found in an image
            (id INTEGER PRIMARY KEY, 
            encoding BLOB);

        CREATE TABLE IF NOT EXISTS ImageEncoding    --A relationship between an image and an encoding
            (id INTEGER PRIMARY KEY, 
            image_id INT,
            encoding_id TEXT,
            FOREIGN KEY (image_id) REFERENCES Image (id),
            FOREIGN KEY (encoding_id) REFERENCES Encoding (id)
            );
                        
        CREATE TABLE IF NOT EXISTS PersonEncoding    --A relationship between an person and an encoding
            (id INTEGER PRIMARY KEY, 
            person_id INT,
            encoding_id INT,
            FOREIGN KEY (person_id) REFERENCES Person (id),
            FOREIGN KEY (encoding_id) REFERENCES Encoding (id)
            );
        
        --Going to happen a lot in bulks
        CREATE INDEX IF NOT EXISTS idx_image_in_db ON Image (filename, date_modified, size_bytes); 
                
        --The intended use case for this entire application
        CREATE INDEX IF NOT EXISTS idx_person_in_images ON ImagePerson (person_id);
        
        CREATE INDEX IF NOT EXISTS idx_encodings_from_image ON ImageEncoding (image_id); 
        """
        self.connection.executescript(create_tables)

        # DEBUG
        if False:
            all_tables = self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view','index') AND name NOT LIKE 'sqlite_%'").fetchall()
            pp(all_tables)

    def add_image(self, image: ImageFile) -> int:
        """
        Adds one image entry to the database.
        :param image: ImageFile to add
        :return: Id of the created image record
        """
        # Check for existence
        exist_check = self.get_image_data_by_attributes(image)
        if exist_check:
            return exist_check.dbid

        # Insert images
        insert_image = """
        INSERT INTO Image (filename, date_modified, size_bytes, path) values (?, ?, ?, ?)
        """
        dbresponse = self.connection.execute(insert_image, self.adapt_ImageFile(image))
        image.dbid = dbresponse.lastrowid
        print(f"Inserted {image} as row {dbresponse.lastrowid}")

        # Insert associated encodings
        for enc in image.encodings_in_image:
            self.add_encoding(enc, image.dbid, image=True)

        # Insert associated people
        for person in image.matched_people:
            self.add_person(person)

        self.connection.commit()
        image.in_database = True
        return image.dbid

    def add_person(self, person: Person) -> int:
        """
        Adds a person to the database.
        :param person: A person object.
        :return: The new person's id
        """
        sql = """
        INSERT INTO Person (name) VALUES (?)
        """
        dbresponse = self.connection.execute(sql, [person.name])
        dbid = dbresponse.lastrowid

        for enc in person.encodings:
            self.add_encoding(enc, associate_id=dbid, person=True)
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

        self.associate_encoding(dbid, associate_id, person, image)
        return dbid

    def associate_encoding(self, encoding_id: int, associate_id: int, person: bool = False, image: bool = False):
        """
        Associate an encoding to a person or image
        :param encoding_id: The id of the encoding to associate
        :param associate_id: The id of the image or person this is associated with
        :param person: Is this associated to a person?
        :param image: Is this associated to an image?
        :return: Id of new association
        """
        # Insert
        if person:
            sql = "INSERT INTO PersonEncoding (encoding_id,person_id) VALUES (?,?)"
        elif image:
            sql = "INSERT INTO ImageEncoding (encoding_id, image_id) VALUES (?,?)"
        else:
            raise ValueError("Must specify a type of encoding association.")
        dbresponse = self.connection.execute(sql, [encoding_id, associate_id])
        dbid = dbresponse.lastrowid
        return dbid

    def get_image_data_by_attributes(self, image: ImageFile) -> Optional[ImageFile]:
        """
        Searches the database for an image with a given filename/date-modified/filesize combination.
        If found, it populates the encodings and people found in the image.
        :param image: The image to check the database for
        :return: Whether the image was found or not
        """
        # Get image
        sql = "SELECT * FROM Image WHERE filename = ? AND date_modified = ? AND size_bytes = ?"
        params = self.adapt_ImageFile(image, include_path=False)
        dbresponse = self.connection.execute(sql, params)
        result = dbresponse.fetchall()

        if len(result) > 1:
            raise Exception(f"Multiple Image records matched the file  '{image.filepath}'")
        if len(result) < 1:
            return None

        image_row = result[0]
        dbid = image_row["id"]

        data_from_db = self.get_image_data_by_id(dbid)
        image.encodings_in_image, image.matched_people = data_from_db

        return image

    def get_image_data_by_id(self, image_id: int) -> (List[ndarray], List[Person]):
        # Don't actually fill input image's data until everything is successfully retrieved

        encodings = self.get_encodings_by_image_id(image_id)
        people = self.get_people_by_image_id(image_id)

        return encodings, people

    def get_encodings_by_image_id(self, image_id: int) -> List[ndarray]:
        sql = """
        SELECT E.encoding
        FROM ImageEncoding IE
        INNER JOIN Encoding E ON IE.encoding_id = E.id
        WHERE IE.image_id = ?
        """
        dbresponse = self.connection.execute(sql, [image_id])
        encoding_rows = dbresponse.fetchall()
        output = []
        for row in encoding_rows:
            output.append(numpy.frombuffer(row["encoding"], dtype="float64"))

        return output

    def get_people_by_image_id(self, image_id: int) -> List[Person]:
        sql = """
                SELECT P.id,P.name
                FROM ImagePerson IP
                INNER JOIN Person P ON IP.person_id = p.id
                WHERE IP.image_id = ?
                """
        dbresponse = self.connection.execute(sql, [image_id])
        results = dbresponse.fetchall()
        return [Person(row["name"]) for row in results]

    # Pseudo-adapters - Don't always want every parameter, so not using the real "adapters" functionality
    @classmethod
    def adapt_ImageFile(cls, image: ImageFile, include_path: bool = True):
        # Date and time stamp of the last time the file was modified
        mtime = datetime.fromtimestamp(os.path.getmtime(image.filepath)).strftime(cls.datetime_format_string)

        # Relative path is last because we won't always use it
        output = [os.path.basename(image.filepath), mtime, os.path.getsize(image.filepath)]
        if include_path:
            output.append(image.filepath)

        return output