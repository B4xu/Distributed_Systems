import os
import requests

base = os.getenv("API_BASE", "http://localhost:8000")

print("Health:", requests.get(f"{base}/health", timeout=5).json())
print("Books:", requests.get(f"{base}/books", timeout=5).json())

resp = requests.post(
    f"{base}/books",
    json={"title": "REST and gRPC in Practice", "author": "Demo Teacher", "year": 2026},
    timeout=5,
)
print("Create:", resp.status_code, resp.json())

print("Book 1:", requests.get(f"{base}/books/1", timeout=5).json())
