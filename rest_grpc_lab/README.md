# Distributed Systems Lab Challenge: Build REST + gRPC Microservices

## Challenge Overview

In this hands-on lab, you will build a complete microservices system from scratch. The system consists of three components that communicate to manage a book catalog:

1. **PostgreSQL Database** - Persistent storage
2. **REST API Service** - External HTTP interface using FastAPI
3. **gRPC Catalog Service** - Internal service communication

**Final Flow**: User → REST API → gRPC Service → PostgreSQL

You will implement all code yourself. No starter code is provided - this is a coding challenge!

## Prerequisites

- Python 3.11+
- Docker + Docker Compose
- Basic knowledge of:
  - REST APIs and HTTP
  - gRPC and Protocol Buffers
  - SQL databases
  - Containerization

## Project Structure to Create

Create the following directory structure:

```
distributed_rest_grpc_demo/
├── proto/
│   └── catalog.proto          # gRPC service definition
├── api_service/
│   └── main.py                # FastAPI REST endpoints
├── catalog_service/
│   └── server.py              # gRPC server implementation
├── scripts/
│   └── init_catalog_db.py     # Database initialization
├── requirements.txt           # Python dependencies
└── docker-compose.yml         # Container orchestration
```

## Lab Point 1: PostgreSQL Database Setup

**Objective**: Set up a PostgreSQL database with a books table.

### Requirements
- Use Docker to run PostgreSQL
- Create a database named `catalog`
- Create a `books` table with columns: `id` (serial primary key), `title` (text), `author` (text), `year` (integer)
- Insert 3 sample books
- Write a Python script to initialize the database

### Steps
1. Start PostgreSQL container with proper environment variables
2. Create `scripts/init_catalog_db.py` to connect and initialize schema
3. Test connection and data insertion

### Testing
```bash
# Check if container is running
docker ps | grep postgres

# Connect and query
psql -h localhost -U catalog_user -d catalog -c "SELECT * FROM books;"
```

## Lab Point 2: REST API Service

**Objective**: Create a FastAPI service that exposes HTTP endpoints for book management.

### Requirements
- Use FastAPI framework
- Implement endpoints:
  - `GET /health` - Health check
  - `GET /books` - List all books
  - `GET /books/{id}` - Get single book
  - `POST /books` - Create new book
- Connect to gRPC service (not database directly)
- Handle errors appropriately (404, 503, etc.)
- Use Pydantic for request validation

### Steps
1. Create `api_service/main.py`
2. Generate gRPC client code from proto file
3. Implement endpoint handlers that call gRPC service
4. Add proper error handling and logging

### Testing
```bash
# Start service (gRPC service must be running)
uvicorn api_service.main:app --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/books
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Book","author":"Test Author","year":2024}'
```

## Lab Point 3: gRPC Catalog Service

**Objective**: Implement a gRPC server that handles book operations and connects to PostgreSQL.

### Requirements
- Use gRPC with Protocol Buffers
- Implement service methods:
  - `Health` - Health check
  - `ListBooks` - Return all books
  - `GetBook` - Return single book by ID
  - `CreateBook` - Add new book
- Connect directly to PostgreSQL database
- Use proper error handling (NOT_FOUND, INVALID_ARGUMENT)
- Implement retry logic for database connections

### Steps
1. Define `proto/catalog.proto` with service and messages
2. Generate Python code from proto file
3. Create `catalog_service/server.py` with gRPC handlers
4. Implement database operations with psycopg2
5. Add connection retry and error handling

### Testing
```bash
# Start service
python catalog_service/server.py

# Check logs for successful startup
# Service should listen on port 50051
```

## Protocol Buffer Definition

You'll need to create `proto/catalog.proto`:

```protobuf
syntax = "proto3";

package catalog;

message Empty {}

message BookId {
  int32 id = 1;
}

message Book {
  int32 id = 1;
  string title = 2;
  string author = 3;
  int32 year = 4;
}

message BookList {
  repeated Book books = 1;
}

message CreateBookRequest {
  string title = 1;
  string author = 2;
  int32 year = 3;
}

service CatalogService {
  rpc Health(Empty) returns (Empty);
  rpc ListBooks(Empty) returns (BookList);
  rpc GetBook(BookId) returns (Book);
  rpc CreateBook(CreateBookRequest) returns (Book);
}
```

## Dependencies (requirements.txt)

```
fastapi==0.116.1
uvicorn[standard]==0.35.0
pydantic==2.11.7
grpcio==1.74.0
grpcio-tools==1.74.0
httpx==0.28.1
psycopg2-binary==2.9.7
```

## Docker Compose Configuration

Create `docker-compose.yml` with services for postgres, catalog-service, and api-service. Include:
- User-defined network
- Health checks
- Proper dependencies
- Volume for postgres data
- Environment variables for database connection

## Full System Integration

Once all components are implemented:

```bash
# Build and run everything
docker compose up --build

# Test the complete system
curl http://localhost:8000/books
```

## Challenge Hints

- **Database**: Use `psycopg2` with `RealDictCursor` for easier data handling
- **gRPC**: Generate stubs with `python -m grpc_tools.protoc`
- **REST**: Use FastAPI's automatic OpenAPI docs at `/docs`
- **Error Handling**: Map gRPC status codes to HTTP status codes
- **Logging**: Add structured logging to all services
- **Health Checks**: Implement both gRPC and HTTP health endpoints

## Success Criteria

- All endpoints return expected responses
- Error cases are handled properly
- Services can be started independently
- Docker compose runs the full system
- Data persists across restarts

## Bonus Challenges

- Add request/response logging
- Implement timeout handling
- Add input validation beyond basic types
- Create unit tests for each service
- Add metrics collection

Good luck! This challenge will test your understanding of microservices, API design, and distributed systems concepts.

- `GET /health`
- `GET /books`
- `GET /books/{id}`
- `POST /books`

Swagger docs:
- `http://<machine-b-ip>:8000/docs`

## 6. Class Demo

### Scenario A — Everything works
1. Start catalog service in one container/process
2. Start REST API service in another container/process
3. By typing curl in terminal or viewing API endpoint in browser:
   - `GET /books`
   - `POST /books`
   - `GET /books/{id}`

### Scenario B — partial failure
1. Leave REST API container/process running
2. Stop Catalog-service container/process
3.  Try fetching `GET /books`
Result:
- REST API runs without catalog-service being active
- dependency is dead
- You will get `503 Service Unavailable`

### Scenario C — latency / timeout
You can implement random time-delay in `catalog_service/server.py`.
With this method you will:
- network timeout
- remote dependency latency
- Why remote call is not same as local function call

## 7. Tests with curl

```bash
curl http://localhost:8000/health
curl http://localhost:8000/books
curl -X POST http://localhost:8000/books -H "Content-Type: application/json" -d "{\"title\":\"Distributed Systems Patterns\",\"author\":\"Demo Author\",\"year\":2026}"
curl http://localhost:8000/books/1
```

## 8. Docker demo

`docker-compose.yml` is for single machine use. Docker will create its own network on host 3 containers each containing: Database, REST API, gRPC respectively.

```bash
docker compose up --build
```

After this operation the service will be available on:
- `http://localhost:8000/docs`

## 9. What we saw making this lab:

- API contract vs implementation
- REST vs gRPC
- service boundary
- persistence
- partial failure
- timeout handling
- why distributed systems are different from local software

## 10. Possible scale-up
### Implement:
- retries
- request IDs
- structured JSON logs
- PostgreSQL
- order-service ცალკე SQLite-ით
- asynchronous messaging
