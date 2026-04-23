#!/usr/bin/env python3
import argparse
import os
import socket
import threading

from common_net import recv_json_line, send_json_line


class ParticipantState:
    def __init__(self, name: str, vote: str, crash_after_prepare: bool):
        self.name = name
        self.vote = vote.upper()
        self.crash_after_prepare = crash_after_prepare
        self.state = "INIT"
        self.locked = False
        self.prepared_value = None

    def log(self, msg: str) -> None:
        print(f"[2PC-{self.name}] {msg}", flush=True)


def handle_request(conn: socket.socket, state: ParticipantState) -> None:
    try:
        msg = recv_json_line(conn)
        if not msg:
            return

        action = msg.get("action")
        txid = msg.get("txid", "unknown")

        if action == "PREPARE":
            value = msg.get("value")
            state.log(f"PREPARE txid={txid} value={value}")

            if state.vote == "NO":
                state.state = "ABORTED"
                state.locked = False
                send_json_line(conn, {
                    "participant": state.name,
                    "txid": txid,
                    "vote": "NO",
                    "state": state.state,
                })
                return

            state.state = "PREPARED"
            state.locked = True
            state.prepared_value = value

            send_json_line(conn, {
                "participant": state.name,
                "txid": txid,
                "vote": "YES",
                "state": state.state,
            })

            if state.crash_after_prepare:
                state.log("Crashing after PREPARE")
                os._exit(1)

        elif action == "COMMIT":
            state.log(f"COMMIT txid={txid}")
            if state.state == "PREPARED":
                state.state = "COMMITTED"
                state.locked = False
            send_json_line(conn, {
                "participant": state.name,
                "txid": txid,
                "result": "ACK_COMMIT",
                "state": state.state,
            })

        elif action == "ABORT":
            state.log(f"ABORT txid={txid}")
            state.state = "ABORTED"
            state.locked = False
            state.prepared_value = None
            send_json_line(conn, {
                "participant": state.name,
                "txid": txid,
                "result": "ACK_ABORT",
                "state": state.state,
            })

        elif action == "STATUS":
            send_json_line(conn, {
                "participant": state.name,
                "state": state.state,
                "locked": state.locked,
                "prepared_value": state.prepared_value,
            })

        else:
            send_json_line(conn, {"error": f"Unknown action: {action}"})

    finally:
        conn.close()


def serve(host: str, port: int, state: ParticipantState) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        state.log(f"Listening on {host}:{port}")

        while True:
            conn, _ = server.accept()
            threading.Thread(target=handle_request, args=(conn, state), daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--vote", choices=["YES", "NO", "yes", "no"], default="YES")
    parser.add_argument("--crash-after-prepare", action="store_true")
    args = parser.parse_args()

    state = ParticipantState(args.name, args.vote, args.crash_after_prepare)
    serve(args.host, args.port, state)


if __name__ == "__main__":
    main()