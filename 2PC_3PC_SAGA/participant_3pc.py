#!/usr/bin/env python3
import argparse
import os
import socket
import threading

from common_net import recv_json_line, send_json_line


class Participant3PC:
    def __init__(self, name: str, vote: str, crash_after_cancommit: bool, crash_after_precommit: bool):
        self.name = name
        self.vote = vote.upper()
        self.crash_after_cancommit = crash_after_cancommit
        self.crash_after_precommit = crash_after_precommit
        self.state = "INIT"
        self.value = None

    def log(self, msg: str) -> None:
        print(f"[3PC-{self.name}] {msg}", flush=True)


def handle_request(conn: socket.socket, state: Participant3PC) -> None:
    try:
        msg = recv_json_line(conn)
        if not msg:
            return

        action = msg.get("action")
        txid = msg.get("txid", "unknown")

        if action == "CAN_COMMIT":
            value = msg.get("value")
            state.log(f"CAN_COMMIT txid={txid} value={value}")

            if state.vote == "NO":
                state.state = "ABORTED"
                send_json_line(conn, {
                    "participant": state.name,
                    "vote": "NO",
                    "state": state.state,
                    "txid": txid,
                })
                return

            state.state = "WAIT"
            state.value = value
            send_json_line(conn, {
                "participant": state.name,
                "vote": "YES",
                "state": state.state,
                "txid": txid,
            })

            if state.crash_after_cancommit:
                state.log("Crashing after CAN_COMMIT")
                os._exit(1)

        elif action == "PRE_COMMIT":
            state.log(f"PRE_COMMIT txid={txid}")
            state.state = "PRECOMMIT"
            send_json_line(conn, {
                "participant": state.name,
                "result": "ACK_PRECOMMIT",
                "state": state.state,
                "txid": txid,
            })

            if state.crash_after_precommit:
                state.log("Crashing after PRE_COMMIT")
                os._exit(1)

        elif action == "DO_COMMIT":
            state.log(f"DO_COMMIT txid={txid}")
            state.state = "COMMITTED"
            send_json_line(conn, {
                "participant": state.name,
                "result": "ACK_COMMIT",
                "state": state.state,
                "txid": txid,
            })

        elif action == "ABORT":
            state.log(f"ABORT txid={txid}")
            state.state = "ABORTED"
            state.value = None
            send_json_line(conn, {
                "participant": state.name,
                "result": "ACK_ABORT",
                "state": state.state,
                "txid": txid,
            })

        elif action == "STATUS":
            send_json_line(conn, {
                "participant": state.name,
                "state": state.state,
                "value": state.value,
            })

        else:
            send_json_line(conn, {"error": f"Unknown action: {action}"})
    finally:
        conn.close()


def serve(host: str, port: int, state: Participant3PC) -> None:
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
    parser.add_argument("--crash-after-cancommit", action="store_true")
    parser.add_argument("--crash-after-precommit", action="store_true")
    args = parser.parse_args()

    state = Participant3PC(
        args.name,
        args.vote,
        args.crash_after_cancommit,
        args.crash_after_precommit,
    )
    serve(args.host, args.port, state)


if __name__ == "__main__":
    main()