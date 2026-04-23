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
    parser.add_argument("--txid", default="tx3pc001")
    parser.add_argument("--value", default="demo-value")
    parser.add_argument("--participant", action="append", required=True,
                        help="NAME:HOST:PORT")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--crash-after-precommit", action="store_true")
    args = parser.parse_args()

    participants = parse_participants(args.participant)

    print(f"[3PC-Coordinator] Start txid={args.txid}", flush=True)

    # Phase 1: CAN_COMMIT
    all_yes = True
    for name, host, port in participants:
        try:
            resp = send_json(host, port, {
                "action": "CAN_COMMIT",
                "txid": args.txid,
                "value": args.value,
            }, timeout=args.timeout)
            print(f"[3PC-Coordinator] CAN_COMMIT {name} -> {resp}", flush=True)
            if resp.get("vote") != "YES":
                all_yes = False
        except Exception as exc:
            print(f"[3PC-Coordinator] CAN_COMMIT error {name}: {exc}", flush=True)
            all_yes = False

    if not all_yes:
        print("[3PC-Coordinator] Some participant said NO or timed out. ABORT.", flush=True)
        for name, host, port in participants:
            try:
                resp = send_json(host, port, {
                    "action": "ABORT",
                    "txid": args.txid,
                }, timeout=args.timeout)
                print(f"[3PC-Coordinator] ABORT {name} -> {resp}", flush=True)
            except Exception as exc:
                print(f"[3PC-Coordinator] ABORT error {name}: {exc}", flush=True)
        return

    # Phase 2: PRE_COMMIT
    precommit_ok = True
    for name, host, port in participants:
        try:
            resp = send_json(host, port, {
                "action": "PRE_COMMIT",
                "txid": args.txid,
            }, timeout=args.timeout)
            print(f"[3PC-Coordinator] PRE_COMMIT {name} -> {resp}", flush=True)
            if resp.get("result") != "ACK_PRECOMMIT":
                precommit_ok = False
        except Exception as exc:
            print(f"[3PC-Coordinator] PRE_COMMIT error {name}: {exc}", flush=True)
            precommit_ok = False

    if not precommit_ok:
        print("[3PC-Coordinator] PRE_COMMIT failed. ABORT.", flush=True)
        for name, host, port in participants:
            try:
                resp = send_json(host, port, {
                    "action": "ABORT",
                    "txid": args.txid,
                }, timeout=args.timeout)
                print(f"[3PC-Coordinator] ABORT {name} -> {resp}", flush=True)
            except Exception as exc:
                print(f"[3PC-Coordinator] ABORT error {name}: {exc}", flush=True)
        return

    if args.crash_after_precommit:
        print("[3PC-Coordinator] Crash after PRE_COMMIT, before DO_COMMIT", flush=True)
        return

    # Phase 3: DO_COMMIT
    for name, host, port in participants:
        try:
            resp = send_json(host, port, {
                "action": "DO_COMMIT",
                "txid": args.txid,
            }, timeout=args.timeout)
            print(f"[3PC-Coordinator] DO_COMMIT {name} -> {resp}", flush=True)
        except Exception as exc:
            print(f"[3PC-Coordinator] DO_COMMIT error {name}: {exc}", flush=True)

    print("[3PC-Coordinator] GLOBAL COMMIT", flush=True)


if __name__ == "__main__":
    main()