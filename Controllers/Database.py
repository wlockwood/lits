import sqlite3

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
