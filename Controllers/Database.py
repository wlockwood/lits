import sqlite3
from typing import List

from Model.ImageFile import ImageFile
from pprint import pprint as pp
import os

from Model.Person import Person


class Database:
    open_connections = []

    def __init__(self, db_file_path: str):
        self.db_file_path = db_file_path
        self.connection = sqlite3.connect(db_file_path)
        self.open_connections.append(self)

    # TODO: Implement initialization
    def initialize(self) -> None:
        """
        Prepare database for first use by creating schema
        """
        # Create tables if they don't already exist: Image, Person, PersonInImage
        raise NotImplementedError()

    def close(self):
        self.connection.close()
        self.open_connections.remove(self)
        print(f"Successfully closed database at {self.db_file_path}")

    @classmethod
    def close_all(cls):
        for c in cls.open_connections:
            c.close()


    def create_schema(self):
        """
        Initializes an empty database.
        :return:
        """
        create_tables = """
        CREATE TABLE IF NOT EXISTS Image    --A single image file per row
            (id INTEGER PRIMARY KEY, filename TEXT, path TEXT, date_modified DATETIME, size_bytes INT);
        """
        self.connection.executescript(create_tables)
        create_tables = """
        CREATE TABLE IF NOT EXISTS Person   --A single individual person per row
            (id INTEGER PRIMARY KEY, name TEXT, encoding TEXT);
        """
        self.connection.executescript(create_tables)
        create_tables = """
        CREATE TABLE IF NOT EXISTS ImagePerson  --A relationship between an image and a person
            (id INTEGER PRIMARY KEY, 
            image_id INT,
            person_id INT,
            FOREIGN KEY (image_id) REFERENCES Image (id), 
            FOREIGN KEY (person_id) REFERENCES Person (id));
        """
        self.connection.executescript(create_tables)
        create_tables = """
        CREATE TABLE IF NOT EXISTS ImageFaceEncoding    --An encoded version of a face found in an image
            (id INTEGER PRIMARY KEY, 
            image_id INT,
            encoding TEXT,
            FOREIGN KEY (image_id) REFERENCES Image (id));
        """
        self.connection.executescript(create_tables)
        create_tables = """
        CREATE INDEX IF NOT EXISTS idx_person_in_images ON ImagePerson (person_id);
        """
        self.connection.executescript(create_tables)
        all_tables = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view','index') AND name NOT LIKE 'sqlite_%'").fetchall()
        pp(all_tables)


    def add_image(self, image: ImageFile):
        # Transform image object into what we need for first script
        # Filling mtime and size here so we get them *after* changes are made.
        image_tuple = (
            os.path.basename(image.filepath),
            image.filepath,
            os.path.getmtime(image.filepath),
            os.path.getsize(image.filepath))

        # Insert images
        insert_image = """
        INSERT INTO Image (filename, path, date_modified, size_bytes) values (?, ?, ?, ?)
        """
        response = self.connection.execute(insert_image, image_tuple).fetchall()
        pp(response)

        # Insert encodings in image
        pass

    def add_people(self, people: List[Person]):
        pass

if __name__ == "__main__":
    test_db_path = "test.db"
    try:
        os.remove(test_db_path)
    except:
        # It's fine if it fails, but it usually won't.
        pass
    test_db = Database(test_db_path)
    test_db.create_schema()

    test_image = ImageFile(r"..\test-image.jpg")
    test_db.add_image(test_image)
    response = test_db.connection.execute("SELECT * FROM Image").fetchall()
    pp(response)