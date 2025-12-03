# mcp/server/fastmcp.py
import asyncio, json, sys, inspect, logging

log = logging.getLogger("fastmcp")
_tools = {}

def tool(name, description, schema=None):
    def decorator(func):
        _tools[name] = {
            "function": func,
            "description": description,
            "schema": schema or {"type": "object", "properties": {}}
        }
        return func
    return decorator

class FastMCP:
    def __init__(self, name):
        self.name = name

    async def _read_message(self, reader):
        header = await reader.readuntil(b'\r\n\r\n')
        header_text = header.decode('utf-8')
        content_length = 0
        for line in header_text.split('\r\n'):
            if line.lower().startswith('content-length:'):
                content_length = int(line.split(':', 1)[1].strip())
                break
        if content_length == 0:
            raise ValueError("Content-Length header not found or is zero.")
        body = await reader.readexactly(content_length)
        return json.loads(body.decode('utf-8'))

    def _write_message(self, writer, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        header = f"Content-Length: {len(body)}\r\n\r\n".encode('utf-8')
        writer.write(header + body)

    async def _handle_request(self, request, writer):
        # ... (이 부분의 로직은 이전과 동일합니다)
        method = request.get("method")
        req_id = request.get("id")
        response = {"jsonrpc": "2.0", "id": req_id}

        if method == "initialize":
            response["result"] = {"serverInfo": {"name": self.name}}
        elif method == "tools/list":
            response["result"] = {
                "tools": [
                    {"name": name, "description": info["description"], "schema": info["schema"]}
                    for name, info in _tools.items()
                ]
            }
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if tool_name in _tools:
                try:
                    tool_func = _tools[tool_name]["function"]
                    if inspect.iscoroutinefunction(tool_func):
                        result = await tool_func(**arguments)
                    else:
                        result = tool_func(**arguments)
                    response["result"] = result
                except Exception as e:
                    response["error"] = {"code": -32000, "message": str(e)}
            else:
                response["error"] = {"code": -32601, "message": "Method not found"}
        else:
             response["error"] = {"code": -32601, "message": "Method not found"}

        self._write_message(writer, response)
        await writer.drain()

    # ✅ 추가: 클라이언트 한 명을 전담해서 처리하는 핸들러
    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        log.info(f"Client connected from {addr}")
        while not reader.at_eof():
            try:
                request = await self._read_message(reader)
                log.info(f"Request from {addr}: {request.get('method')}")
                await self._handle_request(request, writer)
            except (asyncio.IncompleteReadError, ConnectionResetError):
                log.info(f"Client {addr} disconnected.")
                break
            except Exception as e:
                log.error(f"Error handling client {addr}: {e}")
                break
        writer.close()
        await writer.wait_closed()

    # ✅ 변경: stdin/stdout 대신 네트워크 서버를 실행하는 run 메서드
    def run(self, host='127.0.0.1', port=8888):
        async def main():
            server = await asyncio.start_server(self.handle_client, host, port)
            log.info(f"MCP Server starting on {host}:{port}")
            async with server:
                await server.serve_forever()
        
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            log.info("Server is shutting down.")