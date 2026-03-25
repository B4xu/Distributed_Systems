import logging
import os
import time
from concurrent import futures

import grpc
import psycopg2
from psycopg2.extras import RealDictCursor

import catalog_pb2
import catalog_pb2_grpc

DB_HOST = os.getenv("CATALOG_DB_HOST", "localhost")
DB_PORT = int(os.getenv("CATALOG_DB_PORT", "5432"))
DB_NAME = os.getenv("CATALOG_DB_NAME", "catalog")
DB_USER = os.getenv("CATALOG_DB_USER", "catalog_user")
DB_PASSWORD = os.getenv("CATALOG_DB_PASSWORD", "catalog_pass")
GRPC_HOST = os.getenv("CATALOG_GRPC_HOST", "0.0.0.0")
GRPC_PORT = int(os.getenv("CATALOG_GRPC_PORT", "50051"))
SIMULATED_DELAY_MS = int(os.getenv("SIMULATED_DELAY_MS", "0"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("catalog_service")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor,
    )


def ensure_db_ready_and_seed(max_retries=12, delay_seconds=2.0):
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

    for attempt in range(1, max_retries + 1):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema)
                    cur.execute("SELECT COUNT(*) FROM books")
                    row = cur.fetchone()
                    count = row.get("count") if isinstance(row, dict) else row[0]
                    if count == 0:
                        cur.executemany(
                            "INSERT INTO books (title, author, year) VALUES (%s, %s, %s)",
                            seed_rows,
                        )
                    conn.commit()
            logger.info("Postgres database ready and seed applied (attempt %s)", attempt)
            return
        except psycopg2.OperationalError as exc:
            logger.warning(
                "Postgres not ready yet (attempt %s/%s): %s",
                attempt,
                max_retries,
                exc,
            )
            if attempt == max_retries:
                raise
            time.sleep(delay_seconds)


class CatalogService(catalog_pb2_grpc.CatalogServiceServicer):
    def Health(self, request, context):
        return catalog_pb2.Empty()

    def ListBooks(self, request, context):
        if SIMULATED_DELAY_MS > 0:
            time.sleep(SIMULATED_DELAY_MS / 1000.0)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, author, year FROM books ORDER BY id")
                rows = cur.fetchall()

        books = [
            catalog_pb2.Book(
                id=row["id"],
                title=row["title"],
                author=row["author"],
                year=row["year"]
            )
            for row in rows
        ]
        logger.info("ListBooks returned %s rows", len(books))
        return catalog_pb2.BookList(books=books)

    def GetBook(self, request, context):
        if SIMULATED_DELAY_MS > 0:
            time.sleep(SIMULATED_DELAY_MS / 1000.0)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, author, year FROM books WHERE id = %s",
                    (request.id,)
                )
                row = cur.fetchone()

        if row is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Book not found")
            return catalog_pb2.Book()

        logger.info("GetBook id=%s found", request.id)
        return catalog_pb2.Book(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            year=row["year"]
        )

    def CreateBook(self, request, context):
        if not request.title.strip() or not request.author.strip():
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("title and author must be non-empty")
            return catalog_pb2.Book()

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO books (title, author, year) VALUES (%s, %s, %s) RETURNING id",
                    (request.title.strip(), request.author.strip(), int(request.year)),
                )
                book_id = cur.fetchone()["id"]
                conn.commit()

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, author, year FROM books WHERE id = %s",
                    (book_id,)
                )
                row = cur.fetchone()

        logger.info("CreateBook id=%s title=%s", row["id"], row["title"])
        return catalog_pb2.Book(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            year=row["year"]
        )


def serve():
    ensure_db_ready_and_seed()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    catalog_pb2_grpc.add_CatalogServiceServicer_to_server(CatalogService(), server)

    bind_address = f"{GRPC_HOST}:{GRPC_PORT}"
    server.add_insecure_port(bind_address)
    logger.info(
        "Starting gRPC catalog-service on %s with DB %s:%s/%s",
        bind_address,
        DB_HOST,
        DB_PORT,
        DB_NAME,
    )
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
