#!/usr/bin/env python3
import argparse
from typing import List, Tuple

from common_net import send_json


def parse_services(values: List[str]) -> List[Tuple[str, str, int, str, str]]:
    out = []
    for item in values:
        name, host, port, step, compensation = item.split(":")
        out.append((name, host, int(port), step, compensation))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--saga-id", default="saga001")
    parser.add_argument("--service", action="append", required=True,
                        help="NAME:HOST:PORT:STEP:COMPENSATION")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    services = parse_services(args.service)
    completed = []

    print(f"[Saga-Orchestrator] Start saga_id={args.saga_id}", flush=True)

    for name, host, port, step, compensation in services:
        try:
            resp = send_json(host, port, {
                "action": "EXECUTE",
                "saga_id": args.saga_id,
                "step": step,
            }, timeout=args.timeout)
            print(f"[Saga-Orchestrator] EXECUTE {name} -> {resp}", flush=True)

            if resp.get("status") != "DONE":
                raise RuntimeError(f"Step failed on {name}")

            completed.append((name, host, port, step, compensation))
        except Exception as exc:
            print(f"[Saga-Orchestrator] Failure at {name}: {exc}", flush=True)
            print("[Saga-Orchestrator] Starting compensation", flush=True)

            for c_name, c_host, c_port, c_step, c_comp in reversed(completed):
                try:
                    resp = send_json(c_host, c_port, {
                        "action": "COMPENSATE",
                        "saga_id": args.saga_id,
                        "step": c_step,
                        "compensation": c_comp,
                    }, timeout=args.timeout)
                    print(f"[Saga-Orchestrator] COMPENSATE {c_name} -> {resp}", flush=True)
                except Exception as c_exc:
                    print(f"[Saga-Orchestrator] Compensation error {c_name}: {c_exc}", flush=True)

            print("[Saga-Orchestrator] RESULT = COMPENSATED_FAILURE", flush=True)
            return

    print("[Saga-Orchestrator] RESULT = SUCCESS", flush=True)


if __name__ == "__main__":
    main()