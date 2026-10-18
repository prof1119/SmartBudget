# SmartBudget

A local, single-user personal budgeting app built with FastAPI, SQLite, and vanilla JavaScript.

## Features

- Add income and expense transactions with a date, category, and optional note.
- Persistent SQLite storage; records remain after restarting the server.
- Monthly income, expenses, net savings, savings rate, and a 12-month expense chart.
- Create savings goals, update the total saved, and delete goals.
- Choose EGP or USD for display. This changes display formatting only; it does **not** convert values or exchange rates.
- Export transactions to CSV and download a consistent SQLite database backup.
- Input validation and HTML escaping for user-controlled text.

## Run on Windows

Install Python 3.10 or newer, then open PowerShell in this folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat` instead.

Open <http://127.0.0.1:8000>. Keep the terminal open while using the app. Stop the server with `Ctrl+C`.

## Data and backups

The database is `smartbudget.db` in this folder by default. Use the **Backup DB** link in the app regularly and keep backups somewhere else. The **Export CSV** link exports transactions for spreadsheets. Do not delete or replace the database file unless you intend to reset the data.

## Security limits

This is intended for personal use on the same computer. It has no login, user accounts, encryption-at-rest, or multi-user isolation. The server command above binds to `127.0.0.1` so it is not exposed to your local network by default. **Do not expose it directly to the internet or use it for other people's financial data.** Public deployment needs authentication, HTTPS, access controls, secure configuration, and additional testing.

The EGP/USD selector changes only the displayed currency symbol/format. Use one currency consistently for all entries; no conversion is performed.
