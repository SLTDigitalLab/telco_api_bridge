from mcp.server.fastmcp import FastMCP
import json
import os
from contextlib import contextmanager
from filelock import FileLock
from typing import Dict, Any
import uvicorn

# Initialize MCP Server
mcp = FastMCP("loan_management")

DATA_FILE = "loan_data.json"
LOCK_FILE = "loan_data.json.lock"

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
             return {}
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

def save_data(data: Dict[str, Any]):
    """Save data to JSON file safely."""
    with get_data_lock():
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

# --- Tools ---

@mcp.tool()
def get_loan_details(employee_id: str) -> str:
    """
    Returns the current loan status for an employee.
    Includes active loan amount, monthly deduction, and remaining balance.
    """
    data = load_data()
    
    if employee_id not in data:
        return f"Error: Employee ID '{employee_id}' not found in Loan Database."
    
    emp = data[employee_id]
    
    if not emp.get("has_active_loan"):
        return f"{emp['name']} (ID: {employee_id}) does not have any active loans."
    
    return (f"Loan Details for {emp['name']}:\n"
            f"- Original Amount: ${emp['loan_amount']}\n"
            f"- Monthly Deduction: ${emp['monthly_deduction']}\n"
            f"- Remaining Balance: ${emp['remaining_balance']}\n"
            f"- Status: ACTIVE LOAN FOUND. NOT ELIGIBLE for new loans until cleared.")

@mcp.tool()
def apply_for_loan(employee_id: str, amount: int, months: int) -> str:
    """
    Applies for a new loan.
    Business Rules:
    1. Employee must exist.
    2. Employee cannot have an existing active loan.
    """
    with get_data_lock():
        if not os.path.exists(DATA_FILE):
             data = {}
        else:
            with open(DATA_FILE, "r") as f:
                try:
                    data = json.load(f)
                except:
                    data = {}
        
        if employee_id not in data:
             return f"Error: Employee ID '{employee_id}' not found."
        
        emp = data[employee_id]
        
        # Rule: Check for existing loan
        if emp.get("has_active_loan"):
            return (f"REJECTED: {emp['name']} already has an active loan with "
                    f"${emp['remaining_balance']} remaining. You must clear it first.")
        
        # Rule: Process Loan
        emp["has_active_loan"] = True
        emp["loan_amount"] = amount
        emp["remaining_balance"] = amount
        # Simple calculation for monthly deduction (integer division)
        if months > 0:
            emp["monthly_deduction"] = int(amount / months)
        else:
            emp["monthly_deduction"] = amount 

        # Save back to disk
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
            
        return (f"APPROVED: Loan of ${amount} for {months} months has been sanctioned for {emp['name']}. "
                f"Monthly deduction will be ${emp['monthly_deduction']}.")

if __name__ == "__main__":
    # RUNNING ON PORT 8001
    # Note: 'transport="sse"' handles the ASGI app creation automatically.
    # No need for manual Middleware or Uvicorn imports.
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=8001)