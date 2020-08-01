import sqlite3
from pprint import pprint as pp
conn = sqlite3.connect('test.db')
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS images
(id INTEGER PRIMARY KEY, path TEXT, res_x int, res_y int)
""")
c.execute("""
INSERT INTO images (path, res_x, res_y) 
VALUES ('c:\\temp\\pictures', 1024, 768)
""")

results = c.execute("SELECT * FROM images")
all_rows = results.fetchall()
pp(all_rows)

conn.close()
