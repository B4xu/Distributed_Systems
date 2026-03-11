#!/usr/bin/env python3
"""
Lightweight load test client.
Usage: python3 load_test.py <port> <client_id> <msg_rate> [max_msgs]
  max_msgs: optional, stop after sending this many messages (default: unlimited)
"""
import asyncio
import sys

HOST = '127.0.0.1'


async def run_client(port: int, client_id: str, msg_rate: float, max_msgs: int):
    try:
        reader, writer = await asyncio.open_connection(HOST, port)
    except ConnectionRefusedError:
        return

    try:
        name = f"load_client_{client_id}"
        writer.write(name.encode() + b"\n")
        await writer.drain()

        interval = 1.0 / msg_rate if msg_rate > 0 else 999_999
        msg_count = 0

        while max_msgs == 0 or msg_count < max_msgs:
            writer.write(f"msg_{msg_count}".encode() + b"\n")
            await writer.drain()
            msg_count += 1
            await asyncio.sleep(interval)

    except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
        pass
    except Exception:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def main():
    if len(sys.argv) < 4:
        print("Usage: python3 load_test.py <port> <client_id> <msg_rate> [max_msgs]")
        sys.exit(1)

    port = int(sys.argv[1])
    client_id = sys.argv[2]
    msg_rate = float(sys.argv[3])
    max_msgs = int(sys.argv[4]) if len(sys.argv) > 4 else 0  # 0 = unlimited

    await run_client(port, client_id, msg_rate, max_msgs)


if __name__ == '__main__':
    asyncio.run(main())