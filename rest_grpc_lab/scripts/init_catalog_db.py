import os
import psycopg2

DB_HOST = os.getenv("CATALOG_DB_HOST", "localhost")
DB_PORT = int(os.getenv("CATALOG_DB_PORT", "5432"))
DB_NAME = os.getenv("CATALOG_DB_NAME", "catalog")
DB_USER = os.getenv("CATALOG_DB_USER", "catalog_user")
DB_PASSWORD = os.getenv("CATALOG_DB_PASSWORD", "catalog_pass")

schema = """
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INTEGER NOT NULL
);
"""

seed_rows = [
    ("Distributed Systems", "Tanenbaum & van Steen", 2023),
    ("Designing Data-Intensive Applications", "Martin Kleppmann", 2017),
    ("Computer Networks", "Tanenbaum & Wetherall", 2021),
]

conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
conn.autocommit = False

with conn:
    with conn.cursor() as cur:
        cur.execute(schema)
        cur.execute("SELECT COUNT(*) FROM books")
        count = cur.fetchone()[0]
        if count == 0:
            cur.executemany(
                "INSERT INTO books (title, author, year) VALUES (%s, %s, %s)",
                seed_rows
            )

print("Initialized PostgreSQL database %s@%s:%s" % (DB_USER, DB_HOST, DB_PORT))
