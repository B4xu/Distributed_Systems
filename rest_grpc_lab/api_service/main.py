import logging
import os

import grpc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import catalog_pb2
import catalog_pb2_grpc

CATALOG_GRPC_TARGET = os.getenv("CATALOG_GRPC_TARGET", "catalog-service:50051")
GRPC_TIMEOUT_SECONDS = float(os.getenv("GRPC_TIMEOUT_SECONDS", "2.0"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("api_service")

app = FastAPI(title="Book Gateway API", version="1.0.0")


class BookCreate(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    year: int = Field(ge=0, le=3000)


def get_stub():
    channel = grpc.insecure_channel(CATALOG_GRPC_TARGET)
    return catalog_pb2_grpc.CatalogServiceStub(channel)


@app.get("/health")
def health():
    try:
        stub = get_stub()
        stub.Health(catalog_pb2.Empty(), timeout=GRPC_TIMEOUT_SECONDS)
        return {
            "status": "ok",
            "catalog_dependency": "up",
            "grpc_target": CATALOG_GRPC_TARGET
        }
    except grpc.RpcError as exc:
        logger.exception("Health check failed against catalog-service")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "catalog_dependency": "down",
                "grpc_target": CATALOG_GRPC_TARGET,
                "grpc_code": exc.code().name if exc.code() else "UNKNOWN",
                "grpc_details": exc.details(),
            }
        ) from exc


@app.get("/books")
def list_books():
    try:
        stub = get_stub()
        response = stub.ListBooks(catalog_pb2.Empty(), timeout=GRPC_TIMEOUT_SECONDS)
        return [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "year": b.year,
            }
            for b in response.books
        ]
    except grpc.RpcError as exc:
        logger.exception("ListBooks failed")
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Catalog service unavailable",
                "grpc_code": exc.code().name if exc.code() else "UNKNOWN",
                "grpc_details": exc.details(),
            }
        ) from exc


@app.get("/books/{book_id}")
def get_book(book_id: int):
    try:
        stub = get_stub()
        b = stub.GetBook(catalog_pb2.BookId(id=book_id), timeout=GRPC_TIMEOUT_SECONDS)
        return {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "year": b.year,
        }
    except grpc.RpcError as exc:
        logger.exception("GetBook failed for id=%s", book_id)
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Book not found") from exc
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Catalog service unavailable",
                "grpc_code": exc.code().name if exc.code() else "UNKNOWN",
                "grpc_details": exc.details(),
            }
        ) from exc


@app.post("/books", status_code=201)
def create_book(book: BookCreate):
    try:
        stub = get_stub()
        b = stub.CreateBook(
            catalog_pb2.CreateBookRequest(
                title=book.title,
                author=book.author,
                year=book.year,
            ),
            timeout=GRPC_TIMEOUT_SECONDS,
        )
        return {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "year": b.year,
        }
    except grpc.RpcError as exc:
        logger.exception("CreateBook failed")
        if exc.code() == grpc.StatusCode.INVALID_ARGUMENT:
            raise HTTPException(status_code=400, detail=exc.details()) from exc
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Catalog service unavailable",
                "grpc_code": exc.code().name if exc.code() else "UNKNOWN",
                "grpc_details": exc.details(),
            }
        ) from exc
