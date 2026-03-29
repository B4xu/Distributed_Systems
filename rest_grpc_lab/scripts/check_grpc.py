import grpc
import catalog_pb2, catalog_pb2_grpc

stub = catalog_pb2_grpc.CatalogServiceStub(grpc.insecure_channel("localhost:50051"))
print("Health:", stub.Health(catalog_pb2.Empty()))
print("ListBooks:", stub.ListBooks(catalog_pb2.Empty()))
print("GetBook(1):", stub.GetBook(catalog_pb2.BookId(id=1)))
print("CreateBook:", stub.CreateBook(catalog_pb2.CreateBookRequest(title="X", author="Y", year=2026)))
