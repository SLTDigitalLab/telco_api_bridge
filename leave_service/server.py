from mcp.server.fastmcp import FastMCP
import json
import os
from contextlib import contextmanager
from filelock import FileLock
from typing import Dict, Any
import uvicorn

# Initialize MCP Server
mcp = FastMCP("leave_management")

DATA_FILE = "data.json"
LOCK_FILE = "data.json.lock"

# --- Data Persistence Helper ---

@contextmanager
def get_data_lock():
    """Context manager for file locking."""
    lock = FileLock(LOCK_FILE)
    with lock:
        yield

def load_data() -> Dict[str, Any]:
    """Load data from JSON file safely."""
    with get_data_lock():
        if not os.path.exists(DATA_FILE):
             return {"employees": {}}
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"employees": {}}

def save_data(data: Dict[str, Any]):
    """Save data to JSON file safely."""
    with get_data_lock():
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

# --- Tools ---

@mcp.tool()
def get_leave_balance(employee_id: str) -> str:
    """
    Returns the full balance object (Total, Used, Remaining) for the employee.
    """
    data = load_data()
    employees = data.get("employees", {})
    
    if employee_id not in employees:
        return f"Error: Employee ID '{employee_id}' not found."
    
    balance = employees[employee_id].get("leave_balance")
    return json.dumps(balance, indent=2)

@mcp.tool()
def get_leave_history(employee_id: str) -> str:
    """
    Returns the list of leave_records for the employee.
    """
    data = load_data()
    employees = data.get("employees", {})
    
    if employee_id not in employees:
        return f"Error: Employee ID '{employee_id}' not found."
    
    records = employees[employee_id].get("leave_records", [])
    return json.dumps(records, indent=2)

@mcp.tool()
def apply_leave(employee_id: str, start_date: str, days: int, reason: str) -> str:
    """
    Validates balance and applies leave.
    """
    with get_data_lock(): 
        if not os.path.exists(DATA_FILE):
             data = {"employees": {}}
        else:
            with open(DATA_FILE, "r") as f:
                try:
                    data = json.load(f)
                except:
                    data = {"employees": {}}
        
        employees = data.get("employees", {})
        
        if employee_id not in employees:
             return f"Error: Employee ID '{employee_id}' not found."
        
        emp_data = employees[employee_id]
        balance = emp_data["leave_balance"]
        
        if days > balance["remaining"]:
            return f"Error: Insufficient leave balance. Current remaining: {balance['remaining']}, Requested: {days}"
        
        # Apply leave
        balance["remaining"] -= days
        balance["used"] += days
        
        new_record = {
            "start_date": start_date,
            "days": days,
            "reason": reason
        }
        emp_data["leave_records"].append(new_record)
        
        # Save back
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
            
        return f"Success: Leave applied. New remaining balance: {balance['remaining']}"

if __name__ == "__main__":
    # RUNNING ON PORT 8000
    # Clean, simple start command that listens on all interfaces (0.0.0.0)
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=8000)