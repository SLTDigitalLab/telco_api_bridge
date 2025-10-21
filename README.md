📘 Project Documentation
1. Overview

TelMCP is a lightweight Python-based Model Context Protocol (MCP) server that exposes internal telecom APIs to any AI client or MCP-compatible application.
It serves as a middleware bridge between your existing REST APIs and intelligent clients like Claude Desktop, VS Code MCP Extensions, or custom AI agents.

This enables engineers, analysts, and support bots to query telco data (e.g., usage, device, or HR information) in a safe, standardized format without directly hitting internal APIs.

2. Features

🧩 Wraps existing REST APIs into MCP tools.

⚡ Simple async Python server using mcp and httpx.

🧠 Schema validation with pydantic.

🔒 (Optional) Extendable to authentication or rate-limiting later.

🧰 Plug-and-play with any MCP client or IDE.

🧾 Fully typed responses for structured reasoning by AI systems.

3. Current Tools
Tool Name	Description	Input	Output
get_usage_by_subscriber	Retrieves available data usage for a given subscriber ID.	subscriber_id	{subscriber_id, plan, available_mb, as_of}
get_devices_by_subscriber	Returns devices (e.g., routers) associated with a subscriber.	subscriber_id	{subscriber_id, devices:[{id,type,model,status}]}
get_leave_balance	Fetches employee leave balances by employee ID.	employee_id	{employee_id, balances:[{type,available_days}], as_of}
4. Architecture
[MCP Client]
    │
    │  stdio (JSON-RPC)
    ▼
┌───────────────────────────────┐
│          TelMCP Server        │
│  - FastMCP-based Python app   │
│  - Tools: usage, devices, HR  │
│  - Async HTTPX client         │
└───────────────────────────────┘
    │
    ▼
[Internal REST APIs]
(subscribers, employees, devices)

5. Installation
git clone https://github.com/your-org/telmcp.git
cd telmcp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env


Edit .env with your actual base URL:

API_BASE_URL=https://api.yourtelco.lk/v1


Then run:

python server.py

6. Example Interaction (MCP client)

Prompt:

Get available data usage for subscriber 0771234567

Tool call:

{
  "name": "get_usage_by_subscriber",
  "arguments": { "subscriber_id": "0771234567" }
}


Response:

{
  "subscriber_id": "0771234567",
  "plan": "4G Unlimited Home",
  "available_mb": 12456.78,
  "as_of": "2025-10-21T12:05:00Z"
}

7. Adding New Endpoints

To add new APIs, follow the same pattern:

Create a new pydantic model in server.py.

Add a decorated async function with @app.tool.

Call await get_json("/your/new/api/path").

Example:

@app.tool(name="get_billing_summary", description="Retrieve billing info", schema={...})
async def get_billing_summary(ctx: Context, subscriber_id: str):
    raw = await get_json(f"/billing/{subscriber_id}/summary")
    return raw

8. Future Enhancements

OAuth2 or API Key integration

Logging and tracing (OpenTelemetry)

Role-based tool access (employees vs customers)

Docker Compose setup with mock APIs for testing

Rate-limiting per tool

9. Repository Structure
telmcp/
├── server.py           # main MCP server
├── requirements.txt    # dependencies
├── .env.example        # environment config
├── Dockerfile          # optional container setup
└── README.md           # documentation