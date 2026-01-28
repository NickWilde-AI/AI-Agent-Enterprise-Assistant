from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "company.db"
PROJECT_STATUS_PATH = ROOT / "project_status.json"
TICKETS_PATH = ROOT / "outputs" / "tickets.json"

mcp = FastMCP(name="enterprise-assistant-mcp", instructions="Enterprise assistant tools")


def _connect_db() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def _load_project_status() -> dict[str, Any]:
    return json.loads(PROJECT_STATUS_PATH.read_text(encoding="utf-8"))


def _load_tickets() -> dict[str, Any]:
    if not TICKETS_PATH.exists():
        return {"tickets": []}
    return json.loads(TICKETS_PATH.read_text(encoding="utf-8"))


def _write_tickets(payload: dict[str, Any]) -> None:
    TICKETS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@mcp.tool(
    name="get_employee_profile",
    description="根据员工姓名查询部门、职级与邮箱",
)
async def get_employee_profile(name: str) -> dict[str, Any]:
    """Return employee profile info by name."""
    conn = _connect_db()
    cur = conn.cursor()
    cur.execute("SELECT name, department, level, email FROM employees WHERE name = ?", (name,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"found": False, "name": name}
    return {
        "found": True,
        "name": row[0],
        "department": row[1],
        "level": row[2],
        "email": row[3],
    }


@mcp.tool(
    name="get_reimbursement_summary",
    description="查询员工某月的报销总额与明细",
)
async def get_reimbursement_summary(name: str, month: str) -> dict[str, Any]:
    """Return reimbursement details for an employee and month."""
    conn = _connect_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT category, amount, note FROM reimbursements WHERE name = ? AND month = ?",
        (name, month),
    )
    rows = cur.fetchall()
    conn.close()

    items = [{"category": r[0], "amount": r[1], "note": r[2]} for r in rows]
    total = round(sum(item["amount"] for item in items), 2)
    return {"name": name, "month": month, "total": total, "items": items}


@mcp.tool(
    name="get_project_status",
    description="查询指定项目的进度与风险说明",
)
async def get_project_status(project: str) -> dict[str, Any]:
    """Return progress info for a project."""
    payload = _load_project_status()
    for item in payload.get("projects", []):
        if item.get("project") == project:
            return {"found": True, **item}
    return {"found": False, "project": project}


@mcp.tool(
    name="create_ticket",
    description="创建工单记录，返回工单编号",
)
async def create_ticket(title: str, description: str, requester: str, priority: str = "P2") -> dict[str, Any]:
    """Create a ticket in a local JSON file."""
    payload = _load_tickets()
    ticket_id = f"T-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    ticket = {
        "id": ticket_id,
        "title": title,
        "description": description,
        "requester": requester,
        "priority": priority,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    payload.setdefault("tickets", []).append(ticket)
    _write_tickets(payload)
    return {"created": True, "ticket": ticket}


if __name__ == "__main__":
    mcp.run(transport="stdio")
