import sqlite3
from Model.ImageFile import ImageFile

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
        (id INTEGER PRIMARY KEY, filename TEXT, date_modified DATETIME, size_bytes INT)
        
        CREATE TABLE IF NOT EXISTS Person   --A single indvidual person per row
        (id INTEGER PRIMARY KEY, name TEXT)
        
        CREATE TABLE IF NOT EXISTS ImagePerson  --A relationship between an image and a person
        (id INTEGER PRIMARY KEY, image_id INT, person_id INT)
        """
        self.connection.execute(create_tables)