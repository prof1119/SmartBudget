"""SmartBudget: persistent personal finance dashboard powered by FastAPI + SQLite.

Run locally:
    python -m pip install -r requirements.txt
    uvicorn main:app --host 127.0.0.1 --port 8000

Data is stored in smartbudget.db next to this file. Back up that file to back up your data.
This demo is single-user and is not intended to be exposed publicly without authentication,
HTTPS, and deployment-specific security configuration.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, ConfigDict, Field

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("SMARTBUDGET_DB", BASE_DIR / "smartbudget.db"))
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

app = FastAPI(
    title="SmartBudget API",
    description="A single-user personal finance tracker with persistent SQLite storage.",
    version="2.0.0",
)


@contextmanager
def connect_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    with connect_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK(kind IN ('income', 'expense')),
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                occurred_on TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(occurred_on);
            CREATE TABLE IF NOT EXISTS saving_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target REAL NOT NULL CHECK(target > 0),
                saved REAL NOT NULL DEFAULT 0 CHECK(saved >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)


@app.on_event("startup")
def startup() -> None:
    init_db()


class TransactionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    kind: Literal["income", "expense"]
    amount: float = Field(gt=0, le=1_000_000_000, allow_inf_nan=False)
    category: str = Field(min_length=1, max_length=60)
    note: str = Field(default="", max_length=240)
    occurred_on: date = Field(default_factory=date.today)


class GoalCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=80)
    target: float = Field(gt=0, le=1_000_000_000, allow_inf_nan=False)
    saved: float = Field(default=0, ge=0, le=1_000_000_000, allow_inf_nan=False)


class GoalProgress(BaseModel):
    saved: float = Field(ge=0, le=1_000_000_000, allow_inf_nan=False)


def transaction_dict(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "kind": row["kind"], "amount": row["amount"],
            "category": row["category"], "note": row["note"], "occurred_on": row["occurred_on"]}


def goal_dict(row: sqlite3.Row) -> dict:
    target = float(row["target"])
    saved = float(row["saved"])
    return {"id": row["id"], "name": row["name"], "target": target,
            "saved": saved, "percent": round(min(saved / target * 100, 100), 1)}


def dashboard_stats(db: sqlite3.Connection) -> dict:
    month_start = date.today().replace(day=1).isoformat()
    today = date.today().isoformat()
    rows = db.execute("""SELECT kind, COALESCE(SUM(amount), 0) AS total
        FROM transactions WHERE occurred_on >= ? AND occurred_on <= ? GROUP BY kind""", (month_start, today)).fetchall()
    totals = {r["kind"]: float(r["total"]) for r in rows}
    income, expenses = totals.get("income", 0.0), totals.get("expense", 0.0)
    saved = income - expenses
    return {"income": round(income, 2), "expenses": round(expenses, 2),
            "saved": round(saved, 2), "savings_rate": round(saved / income * 100, 1) if income else 0.0}


def monthly_expenses(db: sqlite3.Connection) -> list[dict]:
    today = date.today()
    months: list[tuple[int, int]] = []
    for offset in range(11, -1, -1):
        absolute = today.year * 12 + (today.month - 1) - offset
        months.append((absolute // 12, absolute % 12 + 1))
    start_year, start_month = months[0]
    start = date(start_year, start_month, 1).isoformat()
    results = db.execute("""SELECT substr(occurred_on, 1, 7) AS ym, ROUND(SUM(amount), 2) AS amount
        FROM transactions WHERE kind='expense' AND occurred_on >= ? GROUP BY ym""", (start,)).fetchall()
    totals = {r["ym"]: float(r["amount"] or 0) for r in results}
    return [{"month": f"{MONTHS[m-1]} {str(y)[-2:]}", "amount": round(totals.get(f"{y:04d}-{m:02d}", 0.0), 2)} for y, m in months]


def get_goals(db: sqlite3.Connection) -> list[dict]:
    return [goal_dict(r) for r in db.execute("SELECT * FROM saving_goals ORDER BY id DESC").fetchall()]


@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
def serve_dashboard():
    html_file = BASE_DIR / "smartbudget.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="smartbudget.html not found")
    return HTMLResponse(html_file.read_text(encoding="utf-8"))


@app.get("/api/health", tags=["API"])
def health():
    return {"status": "ok", "storage": "sqlite", "database": DB_PATH.name}


@app.get("/api/backup", tags=["Maintenance"])
def download_database_backup():
    """Create a consistent SQLite snapshot and return it as a downloadable file."""
    init_db()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        backup_path = Path(tmp.name)
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as source, sqlite3.connect(backup_path) as destination:
            source.backup(destination)
        content = backup_path.read_bytes()
        filename = f"smartbudget-backup-{date.today().isoformat()}.db"
        return Response(content=content, media_type="application/vnd.sqlite3",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    finally:
        backup_path.unlink(missing_ok=True)


@app.get("/api/transactions/export.csv", tags=["Maintenance"])
def export_transactions_csv():
    """Export all transactions as UTF-8 CSV for spreadsheet apps."""
    import csv
    import io

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["id", "type", "amount", "category", "date", "note"])
    with connect_db() as db:
        rows = db.execute("SELECT id, kind, amount, category, occurred_on, note FROM transactions ORDER BY occurred_on DESC, id DESC").fetchall()
    writer.writerows([row["id"], row["kind"], row["amount"], row["category"], row["occurred_on"], row["note"]] for row in rows)
    filename = f"smartbudget-transactions-{date.today().isoformat()}.csv"
    return Response("\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.get("/api/dashboard", tags=["API"])
def get_dashboard():
    with connect_db() as db:
        return {"stats": dashboard_stats(db), "monthly_expenses": monthly_expenses(db),
                "saving_goals": get_goals(db),
                "recent_transactions": [transaction_dict(r) for r in db.execute(
                    "SELECT * FROM transactions ORDER BY occurred_on DESC, id DESC LIMIT 20").fetchall()]}


@app.get("/api/transactions", tags=["Transactions"])
def list_transactions(limit: int = Query(default=50, ge=1, le=200)):
    with connect_db() as db:
        return [transaction_dict(r) for r in db.execute(
            "SELECT * FROM transactions ORDER BY occurred_on DESC, id DESC LIMIT ?", (limit,)).fetchall()]


@app.post("/api/transactions", status_code=status.HTTP_201_CREATED, tags=["Transactions"])
def create_transaction(payload: TransactionCreate):
    with connect_db() as db:
        cursor = db.execute("INSERT INTO transactions(kind, amount, category, note, occurred_on) VALUES(?,?,?,?,?)",
            (payload.kind, payload.amount, payload.category, payload.note, payload.occurred_on.isoformat()))
        row = db.execute("SELECT * FROM transactions WHERE id=?", (cursor.lastrowid,)).fetchone()
        return transaction_dict(row)


@app.delete("/api/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Transactions"])
def delete_transaction(transaction_id: int):
    with connect_db() as db:
        cursor = db.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Transaction not found")


@app.get("/api/saving-goals", tags=["Goals"])
def list_goals():
    with connect_db() as db:
        return get_goals(db)


@app.post("/api/saving-goals", status_code=status.HTTP_201_CREATED, tags=["Goals"])
def create_goal(payload: GoalCreate):
    if payload.saved > payload.target:
        raise HTTPException(status_code=422, detail="Saved amount cannot exceed the target")
    with connect_db() as db:
        cursor = db.execute("INSERT INTO saving_goals(name, target, saved) VALUES(?,?,?)",
                            (payload.name, payload.target, payload.saved))
        row = db.execute("SELECT * FROM saving_goals WHERE id=?", (cursor.lastrowid,)).fetchone()
        return goal_dict(row)


@app.patch("/api/saving-goals/{goal_id}", tags=["Goals"])
def update_goal_progress(goal_id: int, payload: GoalProgress):
    with connect_db() as db:
        row = db.execute("SELECT * FROM saving_goals WHERE id=?", (goal_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Saving goal not found")
        if payload.saved > row["target"]:
            raise HTTPException(status_code=422, detail="Saved amount cannot exceed the target")
        db.execute("UPDATE saving_goals SET saved=? WHERE id=?", (payload.saved, goal_id))
        return goal_dict(db.execute("SELECT * FROM saving_goals WHERE id=?", (goal_id,)).fetchone())


@app.delete("/api/saving-goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Goals"])
def delete_goal(goal_id: int):
    with connect_db() as db:
        cursor = db.execute("DELETE FROM saving_goals WHERE id=?", (goal_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Saving goal not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
