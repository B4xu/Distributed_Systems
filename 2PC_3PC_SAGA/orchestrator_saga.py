#!/usr/bin/env python3
import argparse
from typing import List, Tuple

from common_net import send_json


def parse_services(values: List[str]) -> List[Tuple[str, str, int, str, str]]:
    result = []
    for item in values:
        # format: NAME:HOST:PORT:STEP:COMPENSATION
        parts = item.split(":")
        if len(parts) != 5:
            raise ValueError(
                f"Invalid service format: {item}. Expected NAME:HOST:PORT:STEP:COMPENSATION"
            )
        name, host, port, step, compensation = parts[0], parts[1], int(parts[2]), parts[3], parts[4]
        result.append((name, host, port, step, compensation))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Saga Orchestrator")
    parser.add_argument("--saga-id", default="saga001")
    parser.add_argument(
        "--service",
        action="append",
        required=True,
        help="Service in format NAME:HOST:PORT:STEP:COMPENSATION",
    )
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    services = parse_services(args.service)
    completed = []

    print(f"[Orchestrator] Starting saga {args.saga_id}", flush=True)

    for name, host, port, step, compensation in services:
        try:
            print(f"[Orchestrator] EXECUTE step={step} on {name} ({host}:{port})", flush=True)
            resp = send_json(host, port, {
                "action": "EXECUTE",
                "saga_id": args.saga_id,
                "step": step,
            }, timeout=args.timeout)
            print(f"[Orchestrator] Response from {name}: {resp}", flush=True)

            if resp.get("status") != "DONE":
                raise RuntimeError(f"Step failed on {name}: {resp}")

            completed.append((name, host, port, step, compensation))

        except Exception as exc:
            print(f"[Orchestrator] FAILURE at step={step} on {name}: {exc}", flush=True)
            print("[Orchestrator] Starting compensation in reverse order", flush=True)

            for c_name, c_host, c_port, c_step, c_comp in reversed(completed):
                try:
                    print(f"[Orchestrator] COMPENSATE step={c_step} on {c_name}", flush=True)
                    c_resp = send_json(c_host, c_port, {
                        "action": "COMPENSATE",
                        "saga_id": args.saga_id,
                        "step": c_step,
                        "compensation": c_comp,
                    }, timeout=args.timeout)
                    print(f"[Orchestrator] Compensation response from {c_name}: {c_resp}", flush=True)
                except Exception as c_exc:
                    print(f"[Orchestrator] ERROR compensating {c_name}: {c_exc}", flush=True)

            print("[Orchestrator] Saga result: COMPENSATED_FAILURE", flush=True)
            return

    print("[Orchestrator] Saga result: SUCCESS", flush=True)


if __name__ == "__main__":
    main()