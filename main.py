"""
SmartBudget — FastAPI Backend
==============================
Run:
    pip install fastapi uvicorn
    uvicorn main:app --reload --port 8000

Later (PostgreSQL):
    pip install asyncpg databases
    Replace the mock data functions with real DB queries.
"""

import random
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# ─────────────────────────────────────────────
#  App setup
# ─────────────────────────────────────────────
app = FastAPI(
    title="SmartBudget API",
    description="Personal finance dashboard backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
#  Pydantic Schemas  (ready for DB later)
# ─────────────────────────────────────────────
class MonthlyEntry(BaseModel):
    month: str
    amount: float

class SavingGoal(BaseModel):
    name: str
    target: float
    saved: float
    percent: float

class Stats(BaseModel):
    income: float
    expenses: float
    saved: float
    savings_rate: float          # percentage

class DashboardData(BaseModel):
    stats: Stats
    monthly_expenses: List[MonthlyEntry]
    saving_goals: List[SavingGoal]


# ─────────────────────────────────────────────
#  Mock data helpers
#  ─── Swap these functions for DB queries ───
# ─────────────────────────────────────────────
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

GOAL_NAMES = ["Emergency Fund", "Vacation 2026", "New Laptop",
              "Investment", "Car Down Payment"]


def get_stats() -> Stats:
    """
    TODO (PostgreSQL):
        SELECT
            SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) AS income,
            SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expenses
        FROM transactions
        WHERE user_id = :user_id
          AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW());
    """
    income   = round(random.uniform(3500, 6000), 2)
    expenses = round(random.uniform(1800, income * 0.75), 2)
    saved    = round(income - expenses, 2)
    rate     = round((saved / income) * 100, 1)
    return Stats(income=income, expenses=expenses, saved=saved, savings_rate=rate)


def get_monthly_expenses() -> List[MonthlyEntry]:
    """
    TODO (PostgreSQL):
        SELECT
            TO_CHAR(created_at, 'Mon') AS month,
            SUM(amount)               AS amount
        FROM transactions
        WHERE type = 'expense'
          AND user_id = :user_id
          AND created_at >= NOW() - INTERVAL '12 months'
        GROUP BY DATE_TRUNC('month', created_at), month
        ORDER BY DATE_TRUNC('month', created_at);
    """
    return [
        MonthlyEntry(month=m, amount=round(random.uniform(1200, 3500), 2))
        for m in MONTHS
    ]


def get_saving_goals() -> List[SavingGoal]:
    """
    TODO (PostgreSQL):
        SELECT name, target_amount, saved_amount
        FROM saving_goals
        WHERE user_id = :user_id
        ORDER BY created_at;
    """
    goals = []
    for name in random.sample(GOAL_NAMES, k=3):
        target  = round(random.uniform(2000, 15000), 2)
        saved   = round(random.uniform(0, target), 2)
        percent = round((saved / target) * 100, 1)
        goals.append(SavingGoal(name=name, target=target,
                                saved=saved, percent=percent))
    return goals


# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def serve_dashboard():
    """Serve the SmartBudget HTML page."""
    html_file = Path(__file__).parent / "smartbudget.html"
    if not html_file.exists():
        return HTMLResponse("<h2>smartbudget.html not found next to main.py</h2>", status_code=404)
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


@app.get("/api/dashboard", response_model=DashboardData, tags=["API"])
async def get_dashboard():
    """
    Returns all dashboard data in a single request.
    Combine into one endpoint to minimise round-trips from the frontend.
    """
    return DashboardData(
        stats=get_stats(),
        monthly_expenses=get_monthly_expenses(),
        saving_goals=get_saving_goals(),
    )


@app.get("/api/stats", response_model=Stats, tags=["API"])
async def get_stats_only():
    """Income / Expenses / Savings for the current month."""
    return get_stats()


@app.get("/api/monthly-expenses", response_model=List[MonthlyEntry], tags=["API"])
async def get_monthly():
    """12-month expense breakdown for the bar chart."""
    return get_monthly_expenses()


@app.get("/api/saving-goals", response_model=List[SavingGoal], tags=["API"])
async def get_goals():
    """All saving goals with progress percentages."""
    return get_saving_goals()


# ─────────────────────────────────────────────
#  Dev entry-point  (python main.py)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
