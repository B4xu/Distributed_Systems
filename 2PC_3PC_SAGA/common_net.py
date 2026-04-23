import json
import socket
from typing import Any, Dict, Optional


def send_json(host: str, port: int, payload: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        file = sock.makefile("r", encoding="utf-8")
        line = file.readline()
        if not line:
            raise RuntimeError(f"No response from {host}:{port}")
        return json.loads(line)


def recv_json_line(conn: socket.socket) -> Optional[Dict[str, Any]]:
    file = conn.makefile("r", encoding="utf-8")
    line = file.readline()
    if not line:
        return None
    return json.loads(line)


def send_json_line(conn: socket.socket, payload: Dict[str, Any]) -> None:
    conn.sendall((json.dumps(payload) + "\n").encode("utf-8"))