# Railway Reservation System 🚄

A backend reservation engine built with **FastAPI + PostgreSQL** demonstrating core OOP design patterns and database transaction management. Designed as a defendable portfolio project for campus placements.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [OOP Design Patterns](#oop-design-patterns)
- [DBMS Concepts](#dbms-concepts)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
- [Deployment](#deployment)

---

## Features

- Reserve, confirm, and cancel seat bookings with state-aware transitions
- Dynamic pricing based on user type (student discount, senior citizen)
- Row-level locks prevent double-booking under concurrent requests
- Expired hold cleanup releases unconfirmed seats automatically

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python) |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL |
| Deployment | Render (free tier) |

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌────────────┐
│   Client    │────▶│  FastAPI Server  │────▶│ PostgreSQL │
│ (Swagger)   │◀────│  (uvicorn)       │◀────│  (Neon)    │
└─────────────┘     └──────────────────┘     └────────────┘
                           │
                    ┌──────┴──────┐
                    │              │
               ┌────────┐   ┌──────────┐
               │ State  │   │ Strategy │
               │Pattern │   │ Pattern  │
               └────────┘   └──────────┘
```

## OOP Design Patterns

### State Pattern — Booking Lifecycle

Each booking status is encapsulated as its own class implementing a common `BookingState` interface. Transitions are enforced at the type level rather than with if/else blocks.

```
             confirm()
  PENDING ────────────▶ CONFIRMED
     │                    │
     │ cancel()           │ cancel()
     ▼                    ▼
  CANCELLED ◀────────────┘
```

**Key files:** [`app/patterns/state.py`](app/patterns/state.py)

### Strategy Pattern — Dynamic Pricing

Pricing algorithms are interchangeable strategies selected at runtime based on user type. Adding a new discount means writing one new class; zero changes to existing code.

```
         ┌─────────────────────┐
         │   PricingStrategy   │◀──── interface
         └─────────────────────┘
                  ▲
        ┌─────────┼─────────┐
        │         │         │
┌─────────────┐ ┌─────┐ ┌──────────┐
│   Standard  │ │Student│ │  Senior  │
│   Pricing   │ │ 85%   │ │  75%     │
└─────────────┘ └─────┘ └──────────┘
```

**Key files:** [`app/patterns/strategy.py`](app/patterns/strategy.py)

## DBMS Concepts

### Pessimistic Locking (SELECT FOR UPDATE)

When a seat is reserved, the transaction acquires a row-level lock using `SELECT ... FOR UPDATE`. This blocks other concurrent transactions from reading or modifying the same row until the lock is released on commit/rollback.

```sql
BEGIN;
SELECT * FROM seats WHERE id = 1 FOR UPDATE;
-- Other connections must wait here --
UPDATE seats SET is_available = false WHERE id = 1;
COMMIT;  -- Lock released
```

### Normalization (3NF)

Schema is in Third Normal Form — every non-key column depends only on the primary key. No transitive dependencies, no redundant data.

### ACID Transactions

Each booking operation runs inside an explicit database transaction ensuring:
- **Atomicity**: All or nothing
- **Consistency**: Constraints and invariants preserved
- **Isolation**: Locks prevent phantom reads
- **Durability**: Committed writes persist

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/trains` | List all trains |
| GET | `/trains/{id}/seats` | List seats for a train |
| POST | `/bookings/reserve` | Reserve a seat (5-min hold) |
| POST | `/bookings/confirm` | Confirm a pending booking |
| POST | `/bookings/cancel` | Cancel a booking (releases seat) |
| POST | `/admin/cleanup` | Release expired holds |

## Database Schema

```
┌───────────────┐
│     users     │
├───────────────┤
│ id (PK)       │
│ name          │
│ email (UQ)    │
└───────┬───────┘
        │
        │ 1:N
        ▼
┌───────────────┐     ┌───────────────┐
│   bookings    │     │    trains     │
├───────────────┤     ├───────────────┤
│ id (PK)       │     │ id (PK)       │
│ seat_id (FK)  │     │ name          │
│ user_id (FK)  │     │ source        │
│ status        │     │ destination   │
│ price         │     │ base_price    │
│ created_at    │     └───────┬───────┘
│ expires_at    │             │
└───────┬───────┘             │ 1:N
        │                     │
        │ 1:1                 ▼
        ▼             ┌───────────────┐
        │             │     seats     │
        └─────────────┤───────────────┤
                      │ id (PK)       │
                      │ train_id (FK) │
                      │ seat_number   │
                      │ is_available  │
                      └───────────────┘
```

## Getting Started

### Prerequisites

- Python 3.9+

### Setup (SQLite — zero config)

```bash
git clone https://github.com/awakedupex/railway-reservation.git
cd railway-reservation
pip install -r requirements.txt
python3 seed.py
uvicorn app.main:app --reload
```

Visit **http://localhost:8000/docs** for interactive API documentation.

### Setup (PostgreSQL)

```bash
# Set your database URL
echo "DATABASE_URL=postgresql://user:pass@localhost:5432/railway" > .env
python3 seed.py
uvicorn app.main:app --reload
```

## Deployment

### PythonAnywhere (free, no credit card)

1. Sign up at **pythonanywhere.com** with GitHub
2. **Web** tab → **Add a new web app** → **Manual Configuration** → **Python 3.11**
3. Open **Bash console** and run:
```bash
git clone https://github.com/awakedupex/railway-reservation.git
cd railway-reservation
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt gunicorn uvicorn
python seed.py
```
4. Back in **Web** tab → **WSGI configuration file**:
   - Replace contents with: `from wsgi import app`
5. **Virtualenv** section → set path to `/home/yourname/railway-reservation/venv`
6. Click **Reload**

### Render (requires credit card)

1. Push this repo to GitHub
2. Create a PostgreSQL database on [Neon.tech](https://neon.tech) (free)
3. Connect your GitHub repo to [Render](https://render.com)
4. Set `DATABASE_URL` environment variable to your Neon connection string
5. Render auto-detects `render.yaml` and deploys
