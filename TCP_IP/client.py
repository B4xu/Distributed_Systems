import asyncio
import sys

HOST = '127.0.0.1'
PORT = int(sys.argv[1])
NAME = sys.argv[2]


async def main():
    # Retry until server is up
    while True:
        try:
            reader, writer = await asyncio.open_connection(HOST, PORT)
            break
        except ConnectionRefusedError:
            print("Server not ready yet, retrying in 1s...")
            await asyncio.sleep(1)

    print(f"Connected as {NAME}")
    writer.write(NAME.encode() + b"\n")
    await writer.drain()

    receive_task = asyncio.create_task(receive_messages(reader))
    await send_messages(writer)

    receive_task.cancel()
    try:
        await receive_task
    except asyncio.CancelledError:
        pass

    writer.close()
    await writer.wait_closed()


async def receive_messages(reader):
    try:
        while True:
            data = await reader.readline()
            if not data:
                print("[Server closed the connection]")
                break
            print(data.decode(errors='replace').strip())
    except (ConnectionResetError, asyncio.IncompleteReadError):
        print("[Disconnected from server]")


async def send_messages(writer):
    loop = asyncio.get_event_loop()
    try:
        while True:
            # run_in_executor offloads blocking input() so the event loop
            # stays free to receive messages while waiting for user input
            msg = await loop.run_in_executor(None, input)
            writer.write(msg.encode() + b"\n")
            await writer.drain()
    except EOFError:
        pass  # stdin closed (e.g. piped input finished)
    except (ConnectionResetError, BrokenPipeError):
        print("[Lost connection to server]")


asyncio.run(main())