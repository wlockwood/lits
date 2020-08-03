import sqlite3
from Model.ImageFile import ImageFile
from pprint import pprint as pp
import os

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
        
        CREATE TABLE IF NOT EXISTS Person   --A single individual person per row
        (id INTEGER PRIMARY KEY, name TEXT, encoding TEXT);
        
        CREATE TABLE IF NOT EXISTS ImagePerson  --A relationship between an image and a person
        (id INTEGER PRIMARY KEY, image_id INT, person_id INT);
        
        CREATE TABLE IF NOT EXISTS ImageFaceEncoding    --An encoded version of a face found in an image
        (id INTEGER PRIMARY KEY, image_id INT, encoding TEXT);
        
        CREATE INDEX IF NOT EXISTS idx_person_in_images ON ImagePerson (person_id);
        """
        self.connection.executescript(create_tables)
        all_tables = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view','index') AND name NOT LIKE 'sqlite_%'").fetchall()
        pp(all_tables)

if __name__ == "__main__":
    test_db_path = "test.db"
    try:
        os.remove(test_db_path)
    except:
        # It's fine if it fails, but it usually won't.
        pass
    test_db = Database(test_db_path)
    test_db.create_schema()