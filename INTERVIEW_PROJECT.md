# Project-Specific Interview Q&A

## Architecture & Design Decisions

### Q: Why did you choose FastAPI over Django or Spring Boot?

**A:** FastAPI gives me:
- Auto-generated OpenAPI docs (Swagger UI at `/docs`) — zero effort API documentation
- Pydantic models for request/response validation with type hints
- Async support natively, though I use synchronous SQLAlchemy here for simplicity
- Minimal boilerplate — the entire API is ~60 lines of code

Django is heavy for this scope (ORM models, admin panel, forms — none needed). Spring Boot is powerful but has a steeper learning curve with annotations and XML configs. FastAPI hits the sweet spot for a 3rd-year portfolio: modern, lightweight, and production-capable.

### Q: Why synchronous SQLAlchemy instead of async?

**A:** The `SELECT ... FOR UPDATE` pattern works identically in sync and async. Async would add complexity (async session management, `await` chaining) without adding interview value. FastAPI runs sync endpoints in a thread pool, so there's no performance penalty here. For CPU-bound or very high concurrency workloads, I'd switch to async with `asyncpg`.

### Q: Why not use an ORM like Prisma or TypeORM?

**A:** I chose Python's ecosystem. If I were using TypeScript, I'd consider Prisma. But SQLAlchemy is the standard for Python — mature, well-documented, and supports PostgreSQL-specific features like `FOR UPDATE` natively.

---

## Database Schema Decisions

### Q: Why is `seats` a separate table from `trains`? Why not store seat data as a JSON array in trains?

**A:** Two reasons:
1. **Normalization**: JSON arrays violate 1NF — querying "find all available seats on train 1" requires parsing the array in application code instead of a simple `WHERE` clause. With a normalized `seats` table, it's `SELECT * FROM seats WHERE train_id = 1 AND is_available = true`.
2. **Locking granularity**: With a JSON array, `FOR UPDATE` would lock the entire train row — no two users could book different seats simultaneously. With separate seat rows, each seat is locked independently, allowing concurrent bookings on different seats of the same train.

### Q: Why is `status` a string and not a Postgres ENUM type?

**A:** Either works. I used a string for simplicity — no need for `CREATE TYPE` statements. In production, ENUMs offer better type safety and storage efficiency. The state pattern in code already enforces valid transitions; the database layer validates via the `get_state()` function.

### Q: Why a single `bookings` table rather than separate `pending_bookings` and `confirmed_bookings`?

**A:** Single table with a `status` discriminator is simpler — one set of queries, one migration to manage. Partitioning by status (e.g.,`bookings_pending`, `bookings_confirmed`) would optimize query performance at scale but adds operational complexity. For this project's scope, a single table with an index on `status` is correct.

---

## Concurrency & Race Conditions

### Q: What happens if two requests hit `reserve_seat` at the exact same time for the same seat?

**A:** This is exactly what `SELECT ... FOR UPDATE` prevents.

```
Request A arrives first:
  → BEGIN
  → SELECT * FROM seats WHERE id = 1 FOR UPDATE
  → (acquires row lock)

Request B arrives milliseconds later:
  → BEGIN
  → SELECT * FROM seats WHERE id = 1 FOR UPDATE
  → (BLOCKED — waiting for A)

Request A:
  → seat.is_available → True → proceeds
  → creates booking, sets is_available = False
  → COMMIT (releases lock)

Request B:
  → (acquires lock, reads fresh row)
  → seat.is_available → False → raises "Seat is already booked"
  → ROLLBACK
```

A never sees B's data, B never sees A's stale data. The lock serializes access.

### Q: Without `FOR UPDATE`, what would happen?

**A:** Both requests would read `is_available = True` (snapshot isolation). Both would create a booking. You'd have a double-booking — two users hold the same seat. The `FOR UPDATE` lock prevents this by forcing B to wait and re-read after A commits.

### Q: What if the user never confirms — the hold expires?

**A:** The `cleanup_expired_holds()` method runs as a scheduled job. It finds all PENDING bookings where `expires_at < NOW()`, marks them CANCELLED, and releases the seat. During the 5-minute hold window, the seat is unavailable to others — this is intentional to give the user time to complete payment.

### Q: 5 minutes is arbitrary. How would you pick the right timeout?

**A:** It depends on the payment flow. If payment takes 30 seconds, set the hold to 2 minutes. If users enter card details manually, 10 minutes. In production, I'd measure the 95th percentile of payment completion time and set the hold to `p95 × 2` for safety.

---

## Deployment & Operations

### Q: How would you handle rate limiting?

**A:** I'd add a `fastapi-limiter` middleware backed by Redis. Limit to 10 requests/second per IP on booking endpoints. Excessive retries (e.g., bot trying every seat) would get 429 responses.

### Q: How would you monitor this in production?

**A:**
- **Health endpoint**: GET `/` returns `{"status": "running"}`
- **Database connection pool**: SQLAlchemy's pool logs warnings when connections run low
- **Slow queries**: Enable `pg_stat_statements` in PostgreSQL to identify slow queries
- **Application metrics**: Add Prometheus instrumentation via `starlette-exporter`
- **Structured logging**: Replace print with `structlog` for JSON-formatted logs

### Q: What's your CI/CD strategy?

**A:** GitHub Actions:
- On push to `main`: run unit tests, lint with `ruff`, check types with `mypy`
- On merge to `main`: auto-deploy to Render via webhook
- Database migrations handled with `alembic` — auto-generated on schema changes

---

## Edge Cases & Failure Modes

### Q: What happens if the database goes down?

**A:** SQLAlchemy's connection pool will raise `OperationalError`. FastAPI should return HTTP 503 with a retry header. If using async, I'd implement a circuit breaker pattern — after 3 consecutive failures, stop trying and serve a cached response.

### Q: What if a booking is confirmed but the payment fails?

**A:** In this implementation, confirm and payment are separate. Ideally, payment happens *before* confirmation — the flow should be: Reserve → Pay → Confirm. If payment fails after reservation, the hold expires naturally in 5 minutes and the seat is released.

### Q: What if the admin cleanup crashes mid-operation?

**A:** Each booking is processed within the transaction. If the cleanup crashes after processing 5 out of 10 expired bookings, only those 5 are committed. The remaining 5 will be picked up on the next cleanup run because they still satisfy `expires_at < NOW()`. The operation is idempotent.

---

## Personal & Behavioral

### Q: What was the hardest part of building this?

**A:** Getting the concurrency model right. It's easy to write code that works sequentially but fails under load. Understanding `FOR UPDATE`, transaction boundaries, and how PostgreSQL handles locks took the most research. The rest (patterns, routes) was straightforward once the foundation was solid.

### Q: What would you add if you had more time?

**A:**
- **Payment gateway integration** (Stripe/PayPal mock)
- **Redis** for seat hold state instead of DB timestamps (automatic TTL expiry)
- **WebSocket notifications** when seat status changes
- **gRPC** for inter-service communication if this becomes a microservice
- **Load testing** with locust to verify lock contention behavior under 1000 concurrent users
- **Alembic migrations** for schema versioning

### Q: How would you make this production-ready?

**A:**
1. Add authentication (JWT or OAuth2)
2. Replace raw SQLAlchemy with repository pattern + unit of work
3. Add comprehensive test coverage (unit + integration + load tests)
4. Add request rate limiting and DDOS protection
5. Set up monitoring (health checks, metrics, structured logging)
6. Containerize with Docker and use Docker Compose for local dev
7. Database connection pooling with PgBouncer
8. HTTPS with automatic certificate renewal (Let's Encrypt via Render/fly.io)
9. Add idempotency keys on booking endpoints for safe retries

### Q: Why should I hire you based on this project?

**A:** This project demonstrates that I understand:
- **Software design**: I didn't write spaghetti code in route handlers. I separated concerns into patterns (State, Strategy) and services.
- **Database internals**: I know how PostgreSQL handles concurrency — not just CRUD. I can explain isolation levels and lock types.
- **Trade-off thinking**: I chose FastAPI over Django, strings over ENUMs, sync over async — each was a deliberate trade-off I can defend.
- **Production awareness**: I considered deployment, monitoring, edge cases, and failure modes from the start.

Most 3rd-year students build CRUD apps. I built a system that solves hard problems (double-booking, state management) and can talk about why.
