import asyncio
import sys
import time
from datetime import datetime

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
HOST = '127.0.0.1'
MAX_MSG_SIZE = 32
STATS_INTERVAL = 5
MAX_LOG_LINES = 1000

human_clients = set()
load_clients  = set()

server_log = None
chat_log   = None

server_log_lines = 0
chat_log_lines   = 0

human_stats = {}

metrics = {
    'messages_total': 0,
    'bytes_total':    0,
    'messages_last':  0,
    'bytes_last':     0,
    'clients_ever':   0,
    'start_time':     None,
    'last_report':    None,
}


def ts():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def is_load_client(name: str) -> bool:
    return name.startswith("load_client_")


def write_log(f, line, counter_name):
    """Write a line to a log file, rotating it when MAX_LOG_LINES is reached."""
    global server_log_lines, chat_log_lines

    if f is None:
        return

    if counter_name == 'server':
        if server_log_lines >= MAX_LOG_LINES:
            # Rotate: truncate file and start fresh
            f.seek(0)
            f.truncate()
            server_log_lines = 0
        f.write(line + "\n")
        f.flush()
        server_log_lines += 1

    elif counter_name == 'chat':
        if chat_log_lines >= MAX_LOG_LINES:
            f.seek(0)
            f.truncate()
            chat_log_lines = 0
        f.write(line + "\n")
        f.flush()
        chat_log_lines += 1


def log_server(msg):
    """Silent log to server.log only."""
    write_log(server_log, f"[{ts()}] {msg}", 'server')


def log_server_event(msg):
    """Lifecycle events — terminal + server.log."""
    line = f"[{ts()}] {msg}"
    print(line)
    write_log(server_log, line, 'server')


def log_chat(name, text):
    """Human message — chat.log + terminal with per-user count."""
    human_stats[name] = human_stats.get(name, 0) + 1
    line = f"[{ts()}] {name}: {text}"
    write_log(chat_log,   line, 'chat')
    write_log(server_log, line, 'server')
    print(f"{line}  [{name} msgs: {human_stats[name]}]")


async def broadcast(targets, msg: bytes):
    if not targets:
        return
    snapshot = list(targets)
    for c in snapshot:
        try:
            c.write(msg)
        except Exception:
            pass
    await asyncio.gather(*[c.drain() for c in snapshot], return_exceptions=True)


async def print_stats():
    while True:
        await asyncio.sleep(STATS_INTERVAL)
        now   = time.time()
        up    = now - metrics['start_time']
        since = now - metrics['last_report']

        msg_delta  = metrics['messages_total'] - metrics['messages_last']
        byte_delta = metrics['bytes_total']    - metrics['bytes_last']
        msg_rate   = msg_delta  / since if since > 0 else 0
        byte_rate  = byte_delta / since if since > 0 else 0
        avg_msg    = metrics['messages_total'] / up if up > 0 else 0
        avg_byte   = metrics['bytes_total']    / up if up > 0 else 0

        print(f"\n{'─'*60}")
        print(f"  ⏱  Uptime:      {up:.0f}s")
        print(f"  👥 Clients:     {len(human_clients)} human / {len(load_clients)} load / {metrics['clients_ever']} ever")
        print(f"  📨 Messages:    {metrics['messages_total']} total  |  {msg_rate:.1f} msg/s now  |  {avg_msg:.1f} msg/s avg")
        print(f"  📊 Throughput:  {byte_rate/1024:.2f} KB/s now  |  {avg_byte/1024:.2f} KB/s avg")
        print(f"  📦 Bytes in:    {metrics['bytes_total']:,}")
        print(f"  📝 Log lines:   server.log {server_log_lines}/{MAX_LOG_LINES}  |  chat.log {chat_log_lines}/{MAX_LOG_LINES}")
        print(f"{'─'*60}\n")

        metrics['last_report']   = now
        metrics['messages_last'] = metrics['messages_total']
        metrics['bytes_last']    = metrics['bytes_total']


async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    name = None
    load = False
    try:
        name_data = await reader.readline()
        if not name_data:
            return
        name = name_data.decode(errors='replace').strip()
        load = is_load_client(name)
        metrics['clients_ever'] += 1

        if load:
            load_clients.add(writer)
        else:
            human_clients.add(writer)

        log_server_event(f"[+] '{name}' connected from {addr} | "
                         f"humans: {len(human_clients)}  load: {len(load_clients)}")

        while True:
            data = await reader.readline()
            if not data:
                break

            if len(data) > MAX_MSG_SIZE:
                writer.write(b"[server] Message too long, discarded.\n")
                await writer.drain()
                continue

            metrics['messages_total'] += 1
            metrics['bytes_total']    += len(data)
            text = data.decode(errors='replace').strip()

            if load:
                log_server(f"{name}: {text}")
                await broadcast(load_clients - {writer}, (f"{name}: {text}\n").encode())
            else:
                log_chat(name, text)
                await broadcast(human_clients - {writer}, (f"{name}: {text}\n").encode())

    except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
        pass
    finally:
        load_clients.discard(writer)
        human_clients.discard(writer)
        display_name = name or str(addr)
        log_server_event(f"[-] '{display_name}' disconnected | "
                         f"humans: {len(human_clients)}  load: {len(load_clients)}")
        if not load and display_name in human_stats:
            print(f"    {display_name} sent {human_stats[display_name]} message(s) total.")
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def main():
    global server_log, chat_log, server_log_lines, chat_log_lines
    metrics['start_time']  = time.time()
    metrics['last_report'] = time.time()

    # Open in r+ if exists to count existing lines, else create fresh
    import os
    for fname, counter in [("server.log", "server"), ("chat.log", "chat")]:
        if os.path.exists(fname):
            with open(fname, 'r') as f:
                lines = sum(1 for _ in f)
            if counter == 'server':
                server_log_lines = min(lines, MAX_LOG_LINES)
            else:
                chat_log_lines = min(lines, MAX_LOG_LINES)

    server_log = open("server.log", "a")
    chat_log   = open("chat.log",   "a")

    try:
        server = await asyncio.start_server(handle_client, HOST, PORT)
        actual_port = server.sockets[0].getsockname()[1]
        log_server_event(f"Server started on {HOST}:{actual_port}")
        print(f"Server running on port {actual_port}")
        print(f"Human chat → chat.log  (printed here with per-user counts)")
        print(f"Load test  → server.log only (silent in terminal)")
        print(f"Log limit:   {MAX_LOG_LINES} lines per file (rotates when full)")
        print(f"Stats every {STATS_INTERVAL}s\n")

        asyncio.create_task(print_stats())
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        log_server_event("Server shutting down.")
    finally:
        if human_stats:
            print("\n=== Session Summary ===")
            for user, count in sorted(human_stats.items()):
                print(f"  {user}: {count} message(s)")
        server_log.close()
        chat_log.close()


asyncio.run(main())