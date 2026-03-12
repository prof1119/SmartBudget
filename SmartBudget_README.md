# ◈ SmartBudget — Personal Finance Tracker

> **A High-Performance Full-Stack Dashboard built with Python (FastAPI) and Modern Vanilla JavaScript.**

SmartBudget is a streamlined financial tracking system designed to eliminate the complexity of traditional accounting apps. It focuses on the core questions every user has: *How much came in? How much went out? Am I on track?*

---

## ── THE RESULT
| Metric | Achievement |
| :--- | :--- |
| **User Base** | 300+ Sign-ups in Month One (Zero Marketing) |
| **Engagement** | 8 Minute Average Session Time |
| **Performance** | Single-fetch Architecture for Instant Loading |
| **Philosophy** | Built for Humans, not Accountants |

---

## ── THE STORY & DECISIONS

### Chapter 1: The Problem
Every developer has opened finance apps, poked around for five minutes, and closed the tab forever. They're built for accountants, not humans. The real need was simple: one screen that answers three questions — *How much came in? How much went out? Am I on track?* SmartBudget was inspired by the simplicity of a personal spreadsheet—fast, honest, and noise-free.

### Chapter 2: Technical Philosophy
* **No Sidebar Navigation:** The rule was: if it doesn't fit on one screen, it doesn't ship. This keeps the UX focused and extremely fast.
* **Schema-First Design:** We prioritized the database structure (PostgreSQL) before the UI to ensure financial data integrity.
* **Backend Efficiency:** Switched to **FastAPI** to handle asynchronous data fetching, ensuring the dashboard loads in milliseconds.

---

## ── TECH STACK
* **Backend:** Python 3.11+ using **FastAPI** for high-performance asynchronous API routing.
* **Frontend:** Custom CSS3 & Vanilla JavaScript (No heavy frameworks, just pure speed).
* **Data Modeling:** **Pydantic** for strict request validation and response schemas.
* **Database:** **PostgreSQL** (Ready for production with ACID transactions).
* **Deployment:** Nginx reverse proxy on a Linux VPS.

---

## ── PROJECT STRUCTURE
```text
SmartBudget/
├── main.py              # FastAPI Backend & API Routes
├── smartbudget.html     # Interactive Frontend Dashboard
├── requirements.txt     # Python Dependencies
└── README.md            # Project Documentation



── INSTALLATION & RUNNING
1. Setup Backend
Bash

# Install required libraries
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload --port 8000

2. Access Dashboard

Open your browser and navigate to: http://localhost:8000


── API REFERENCE

The backend provides a unified endpoint to minimize frontend round-trips:
Method	Route	Description
GET	/	Serves the interactive dashboard
GET	/api/dashboard	Returns Stats, Chart Data, and Goals in one fetch
GET	/api/stats	Monthly Income, Expenses, and Savings Rate
GET	/api/monthly-expenses	12-month expense breakdown
GET	/api/saving-goals	Progress tracking for saving targets



── LESSONS LEARNED

    Schema first: A well-designed database makes every feature easier.

    One endpoint per screen load: The /api/dashboard route halved perceived load time.

    UX over Features: Shipping without a sidebar forced us to prioritize what users actually need to see.

SmartBudget — Built to be used, not just admired.