#!/usr/bin/env python3
import argparse
from typing import List, Tuple

from common_net import send_json


def parse_participants(values: List[str]) -> List[Tuple[str, str, int]]:
    out = []
    for item in values:
        name, host, port = item.split(":")
        out.append((name, host, int(port)))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--txid", default="tx001")
    parser.add_argument("--value", default="demo-value")
    parser.add_argument("--participant", action="append", required=True,
                        help="NAME:HOST:PORT")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--crash-after-yes", action="store_true")
    args = parser.parse_args()

    participants = parse_participants(args.participant)

    print(f"[2PC-Coordinator] Start txid={args.txid}", flush=True)

    votes = []
    all_yes = True

    for name, host, port in participants:
        try:
            resp = send_json(host, port, {
                "action": "PREPARE",
                "txid": args.txid,
                "value": args.value,
            }, timeout=args.timeout)
            print(f"[2PC-Coordinator] {name} -> {resp}", flush=True)
            vote = resp.get("vote")
            votes.append((name, vote))
            if vote != "YES":
                all_yes = False
        except Exception as exc:
            print(f"[2PC-Coordinator] {name} error: {exc}", flush=True)
            votes.append((name, "NO_RESPONSE"))
            all_yes = False

    print(f"[2PC-Coordinator] Votes: {votes}", flush=True)

    if all_yes:
        if args.crash_after_yes:
            print("[2PC-Coordinator] Crash after all YES, before COMMIT", flush=True)
            return

        for name, host, port in participants:
            try:
                resp = send_json(host, port, {
                    "action": "COMMIT",
                    "txid": args.txid,
                }, timeout=args.timeout)
                print(f"[2PC-Coordinator] COMMIT ACK {name} -> {resp}", flush=True)
            except Exception as exc:
                print(f"[2PC-Coordinator] COMMIT error {name}: {exc}", flush=True)

        print("[2PC-Coordinator] GLOBAL COMMIT", flush=True)
    else:
        for name, host, port in participants:
            try:
                resp = send_json(host, port, {
                    "action": "ABORT",
                    "txid": args.txid,
                }, timeout=args.timeout)
                print(f"[2PC-Coordinator] ABORT ACK {name} -> {resp}", flush=True)
            except Exception as exc:
                print(f"[2PC-Coordinator] ABORT error {name}: {exc}", flush=True)

        print("[2PC-Coordinator] GLOBAL ABORT", flush=True)


if __name__ == "__main__":
    main()