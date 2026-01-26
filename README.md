# 🤖 HR Agent

An AI-powered HR assistant using **MCP (Model Context Protocol)** to provide leave management, loan processing, and HR policy search through natural conversation.

## 🏗️ Architecture

```
Claude Desktop ──► bridge.py ──► Orchestrator (Local) ──┬──► Leave Service (Docker)
                                                        ├──► Loan Service (Docker)
React Frontend ─────────────────► Orchestrator (Local) ─┴──► Policy Service (Docker + RAG)
```

- **Orchestrator**: Runs locally on your machine (port 8005)
- **MCP Services**: Run in Docker containers (ports 8000, 8001, 8002)

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- OpenAI API Key

### 1. Configure Environment

```bash
# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your-key-here" > .env
```

### 2. Start MCP Services (Docker)

```bash
docker-compose up -d --build
```

### 3. Start Orchestrator (Local)

```bash
cd orchestrator
pip install -r requirements.txt

# Set environment variable (PowerShell)
$env:OPENAI_API_KEY="your-key-here"

# Run the orchestrator
python main.py
```

---

## 🌐 Access Points

| Service | Port | Location | Description |
|---------|------|----------|-------------|
| Orchestrator | `8005` | Local | Main API + MCP endpoint |
| Leave Service | `8000` | Docker | Leave management |
| Loan Service | `8001` | Docker | Loan processing |
| Policy Service | `8002` | Docker | RAG policy search |

---

## 🛠️ Available Tools

### Leave Service
- `get_leave_balance(employee_id)` - Get leave balance
- `get_leave_history(employee_id)` - View leave records
- `apply_leave(employee_id, start_date, days, reason)` - Apply for leave

### Loan Service
- `get_loan_details(employee_id)` - Check loan status
- `apply_for_loan(employee_id, amount, months)` - Apply for loan

### Policy Service
- `search_hr_policies(query)` - Search HR policy documents

---

## Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hr-agent": {
      "command": "python",
      "args": ["<path-to>/bridge.py", "http://localhost:8005/mcp"]
    }
  }
}
```

---

## Project Structure

```
HR Agent/
├── orchestrator/       # Main API gateway (runs locally)
├── leave_service/      # Leave management (Docker)
├── loan_service/       # Loan processing (Docker)
├── policy_service/     # RAG policy search (Docker)
├── frontend-client/    # React web UI
├── bridge.py           # Claude Desktop MCP bridge
└── docker-compose.yml  # Docker config for MCP services
```

---

## 📄 Adding Policy Documents

Place PDF, DOCX, or TXT files in `policy_service/docs/` and restart:

```bash
docker-compose restart policy_service
```

---

## Troubleshooting

```bash
# View MCP service logs
docker-compose logs -f

# Rebuild services from scratch
docker-compose down && docker-compose up --build -d

# Check if orchestrator can reach services
curl http://localhost:8000/sse
curl http://localhost:8001/sse
curl http://localhost:8002/sse
```

