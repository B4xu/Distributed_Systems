#!/usr/bin/env python3
import argparse
import socket
import threading

from common_net import recv_json_line, send_json_line


class SagaServiceState:
    def __init__(self, name: str, fail_action: str):
        self.name = name
        self.fail_action = fail_action
        self.completed = []

    def log(self, msg: str) -> None:
        print(f"[Saga-{self.name}] {msg}", flush=True)


def handle_request(conn: socket.socket, state: SagaServiceState) -> None:
    try:
        msg = recv_json_line(conn)
        if not msg:
            return

        action = msg.get("action")
        saga_id = msg.get("saga_id", "unknown")

        if action == "EXECUTE":
            step = msg.get("step")
            state.log(f"EXECUTE step={step} saga_id={saga_id}")

            if step == state.fail_action:
                send_json_line(conn, {
                    "service": state.name,
                    "saga_id": saga_id,
                    "status": "FAILED",
                    "step": step,
                })
                return

            state.completed.append(step)
            send_json_line(conn, {
                "service": state.name,
                "saga_id": saga_id,
                "status": "DONE",
                "step": step,
            })

        elif action == "COMPENSATE":
            step = msg.get("step")
            comp = msg.get("compensation")
            state.log(f"COMPENSATE step={step} comp={comp} saga_id={saga_id}")

            if step in state.completed:
                state.completed.remove(step)

            send_json_line(conn, {
                "service": state.name,
                "saga_id": saga_id,
                "status": "COMPENSATED",
                "step": step,
                "compensation": comp,
            })

        elif action == "STATUS":
            send_json_line(conn, {
                "service": state.name,
                "completed": list(state.completed),
            })

        else:
            send_json_line(conn, {"error": f"Unknown action: {action}"})
    finally:
        conn.close()


def serve(host: str, port: int, state: SagaServiceState) -> None:
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
    parser.add_argument("--fail-action", default="")
    args = parser.parse_args()

    state = SagaServiceState(args.name, args.fail_action)
    serve(args.host, args.port, state)


if __name__ == "__main__":
    main()