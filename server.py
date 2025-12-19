# server.py
import os, sys, argparse, asyncio
from typing import List, Optional

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

# ---- logging to stderr only ----
def log(*args):
    sys.stderr.write(" ".join(str(a) for a in args) + "\n")
    sys.stderr.flush()

load_dotenv()
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8080")
TIMEOUT = float(os.getenv("HTTP_TIMEOUT_SECONDS", "8"))

# ---------- Pydantic models ----------
class UsageResponse(BaseModel):
    subscriber_id: str
    plan: Optional[str] = None
    available_mb: float
    as_of: str

class DeviceItem(BaseModel):
    id: str
    type: str
    model: Optional[str] = None
    serial: Optional[str] = None
    status: Optional[str] = None

class DevicesResponse(BaseModel):
    subscriber_id: str
    devices: List[DeviceItem]

class LeaveBucket(BaseModel):
    type: str
    available_days: float

class LeaveResponse(BaseModel):
    employee_id: str
    balances: List[LeaveBucket]
    as_of: str

# ---------- HTTP helper ----------
async def get_json(path: str):
    url = f"{API_BASE.rstrip('/')}{path}"
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()

# ---------- MCP server ----------
app = FastMCP("telmcp-python")

@app.tool(name="get_usage_by_subscriber", description="Get available data usage for a subscriber.")
async def get_usage_by_subscriber(subscriber_id: str) -> dict:
    """Return available data usage for the given subscriber_id."""
    raw = await get_json(f"/subscribers/{subscriber_id}/usage")
    data = UsageResponse.model_validate(raw)
    return data.model_dump()

@app.tool(name="get_devices_by_subscriber", description="List devices (e.g., routers) for a subscriber.")
async def get_devices_by_subscriber(subscriber_id: str) -> dict:
    """Return device/router info for the given subscriber_id."""
    raw = await get_json(f"/subscribers/{subscriber_id}/devices")
    data = DevicesResponse.model_validate(raw)
    return data.model_dump()

@app.tool(name="get_leave_balance", description="Get an employee's leave balances.")
async def get_leave_balance(employee_id: str) -> dict:
    """Return leave balances for the given employee_id."""
    raw = await get_json(f"/employees/{employee_id}/leave-balance")
    data = LeaveResponse.model_validate(raw)
    return data.model_dump()

@app.tool(name="health", description="Health check.")
async def health() -> dict:
    return {"status": "ok"}

# ---------- CLI entry ----------
async def _selftest():
    log("SELFTEST against", API_BASE)
    try:
        usage = await get_usage_by_subscriber("0771234567")
        log("usage:", usage)
    except Exception as e:
        log("usage failed:", e)

    try:
        devs = await get_devices_by_subscriber("0771234567")
        log("devices:", devs)
    except Exception as e:
        log("devices failed:", e)

    try:
        leave = await get_leave_balance("EMP00123")
        log("leave:", leave)
    except Exception as e:
        log("leave failed:", e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TelMCP server")
    parser.add_argument("--selftest", action="store_true",
                        help="Run tools directly (no JSON-RPC/stdio). Safe for terminals.")
    args = parser.parse_args()

    if args.selftest:
        asyncio.run(_selftest())
    else:
        # stdio mode: DO NOT print to stdout
        app.run()
