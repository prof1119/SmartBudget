from datetime import date

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "smartbudget-test.db")
    with TestClient(main.app) as test_client:
        yield test_client


def test_transaction_persists_and_updates_dashboard(client):
    income = client.post("/api/transactions", json={
        "kind": "income", "amount": 1200, "category": "Work", "note": "Pay",
        "occurred_on": date.today().isoformat(),
    })
    expense = client.post("/api/transactions", json={
        "kind": "expense", "amount": 250, "category": "Food",
        "occurred_on": date.today().isoformat(),
    })
    assert income.status_code == 201
    assert expense.status_code == 201

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["stats"]["income"] == 1200
    assert dashboard.json()["stats"]["expenses"] == 250
    assert dashboard.json()["stats"]["saved"] == 950
    assert len(dashboard.json()["recent_transactions"]) == 2


def test_invalid_amount_is_rejected(client):
    response = client.post("/api/transactions", json={
        "kind": "expense", "amount": -1, "category": "Food",
        "occurred_on": date.today().isoformat(),
    })
    assert response.status_code == 422


def test_saving_goal_progress_and_limits(client):
    created = client.post("/api/saving-goals", json={
        "name": "Laptop", "target": 1000, "saved": 100,
    })
    assert created.status_code == 201
    goal_id = created.json()["id"]

    updated = client.patch(f"/api/saving-goals/{goal_id}", json={"saved": 400})
    assert updated.status_code == 200
    assert updated.json()["percent"] == 40

    invalid = client.patch(f"/api/saving-goals/{goal_id}", json={"saved": 1001})
    assert invalid.status_code == 422


def test_export_and_backup_endpoints(client):
    client.post("/api/transactions", json={
        "kind": "income", "amount": 300, "category": "Test",
        "occurred_on": date.today().isoformat(),
    })
    exported = client.get("/api/transactions/export.csv")
    backup = client.get("/api/backup")
    assert exported.status_code == 200
    assert "category" in exported.text
    assert backup.status_code == 200
    assert backup.content.startswith(b"SQLite format 3")
