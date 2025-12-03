# server.py
import os, sys, json, logging
import httpx
from typing import Optional
from mcp.server.fastmcp import FastMCP, tool

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("serviceplex-mcp")

BASE_URL = os.getenv("BASE_URL", "https://dev-api.serviceplex.ai")

# 💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡
# ✅ 변경: 환경 변수 대신 코드에 직접 False를 지정하여 SSL 검증을 항상 비활성화합니다.
VERIFY_SSL = False
# 💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡

TIMEOUT = httpx.Timeout(10.0)

mcp = FastMCP("serviceplex-mcp")

def _client(token: str = None) -> httpx.AsyncClient:
    headers = {
        "Basic-Key": "c2VydmljZXBsZXhCYXNpY0tleQ=="
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    return httpx.AsyncClient(
        base_url=BASE_URL, headers=headers, verify=VERIFY_SSL, timeout=TIMEOUT
    )

@tool(name="health.ping", description="Simple liveness check.")
async def health_ping() -> dict:
    return {"ok": True, "base_url": BASE_URL, "verify_ssl": VERIFY_SSL}

@tool(
    name="serviceplex.get_contract",
    description="Fetch contract detail by WBS Code.",
    schema={"type":"object","properties":{
        "wbsCode":{"type":"string"}
    },"required":["wbsCode"]}
)
async def serviceplex_get_contract(wbsCode: str):
    async with _client() as cli:
        params = {"wbsCode": wbsCode}
        r = await cli.get("/inbound/api/mcp/cntrcts", params=params)
        r.raise_for_status()
        response_data = r.json()
        return response_data.get("data", {}).get("cntrct", {})

if __name__ == "__main__":
    log.info(f"Configuring MCP Server. BASE_URL={BASE_URL}, VERIFY_SSL={VERIFY_SSL}")
    mcp.run(host="0.0.0.0", port=8888)