# mcp_client.py
import asyncio
import json, time

async def send(writer, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("utf-8")
    writer.write(header + data)
    await writer.drain()

async def recv(reader, timeout=10):
    try:
        header = await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'), timeout=timeout)
        header_text = header.decode("utf-8", errors="replace")
        content_length = None
        for line in header_text.split("\r\n"):
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":", 1)[1].strip())
                break
        if content_length is None:
            raise RuntimeError("invalid Content-Length")

        body = await asyncio.wait_for(reader.readexactly(content_length), timeout=timeout)
        return json.loads(body.decode("utf-8"))
    except asyncio.TimeoutError:
        raise TimeoutError("Read operation timed out.")
    except (asyncio.IncompleteReadError, ConnectionResetError):
        raise RuntimeError("Server closed the connection.")


async def main():
    host = '127.0.0.1'
    port = 8888
    try:
        print(f"[client] Connecting to {host}:{port} ...")
        reader, writer = await asyncio.open_connection(host, port)
    except ConnectionRefusedError:
        print(f"[client] Connection failed. Is the server running on {host}:{port}?")
        return
        
    print("[client] Connection successful.")

    print("\n[client] sending initialize ...")
    await send(writer, {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"clientInfo": { "name": "network-test", "version": "0.0.2" }}
    })
    print("[client] initialize OK:", await recv(reader))

    print("\n[client] tools/list ...")
    await send(writer, {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
    print(json.dumps(await recv(reader), indent=2, ensure_ascii=False))

    print("\n[client] call health.ping ...")
    await send(writer, {
        "jsonrpc":"2.0","id":3,"method":"tools/call",
        "params":{"name":"health.ping","arguments":{}}
    })
    print(json.dumps(await recv(reader), indent=2, ensure_ascii=False))

    print("\n[client] call serviceplex.get_contract ...")
    await send(writer, {
        "jsonrpc":"2.0","id":4,"method":"tools/call",
        "params":{
            "name":"serviceplex.get_contract",
            "arguments":{"wbsCode":"B.220410.3.1"}
        }
    })
    print(json.dumps(await recv(reader), indent=2, ensure_ascii=False))
    
    print("\n[client] Closing connection.")
    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())