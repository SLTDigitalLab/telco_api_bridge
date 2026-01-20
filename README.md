# 🤖 HR Agent

An AI-powered HR assistant using **MCP (Model Context Protocol)** to provide leave management, loan processing, and HR policy search through natural conversation.

<img width="578" height="447" alt="HR_Agent diagram" src="https://github.com/user-attachments/assets/52ca74c1-7d8a-4521-bca4-db5b8544bfd0" />

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key

### Setup

```bash
# 1. Configure environment
echo "OPENAI_API_KEY=your-key-here" > .env

# 2. Start all services
docker-compose up --build
```

### Access Points

| Service | Port | Description |
|---------|------|-------------|
| Orchestrator | `8005` | Main API + MCP endpoint |
| Leave Service | `8000` | Leave management |
| Loan Service | `8001` | Loan processing |
| Policy Service | `8002` | RAG policy search |

---

## Available Tools

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
├── orchestrator/       # Central API gateway (FastAPI + MCP)
├── leave_service/      # Leave management microservice
├── loan_service/       # Loan processing microservice
├── policy_service/     # RAG-based policy search
├── frontend-client/    # React web UI
├── bridge.py           # Claude Desktop MCP bridge
└── docker-compose.yml
```

---

## Adding Policy Documents

Place PDF, DOCX, or TXT files in `policy_service/docs/` and restart:

```bash
docker-compose restart policy_service
```

---

## Troubleshooting

```bash
# View logs
docker-compose logs -f

# Rebuild from scratch
docker-compose down && docker-compose up --build
```
