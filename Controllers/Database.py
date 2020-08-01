import sqlite3

class Database:
    def __init__(self, db_file_path: str):
        self.db_file_path = db_file_path
        self.connection = sqlite3.connect(db_file_path)

    def close(self):
        self.connection.close()

