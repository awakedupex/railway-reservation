# DBMS Interview Q&A

## ACID Transactions

### Q: Explain ACID with an example from your project.

**A:**

| Property | How it applies |
|----------|---------------|
| **Atomicity** | When reserving a seat, both `seat.is_available = False` and `booking = Booking(...)` happen together or not at all. If the server crashes after writing the booking but before updating the seat, the transaction rolls back entirely. |
| **Consistency** | Foreign key constraints ensure every booking references a valid seat and user. The unique seat-number-per-train constraint prevents duplicate seat configurations. |
| **Isolation** | `SELECT ... FOR UPDATE` ensures concurrent reservations see a consistent view — no two transactions can both think a seat is available. |
| **Durability** | Once `COMMIT` returns, the data is persisted to disk even if the server loses power immediately after. |

### Q: What isolation level does PostgreSQL use by default? What level do you use?

**A:** PostgreSQL defaults to **READ COMMITTED**. In READ COMMITTED, a `SELECT ... FOR UPDATE` will block until the locking transaction completes, then re-read the row. This is sufficient for our booking system because we hold the lock until commit.

For stricter guarantees (e.g., preventing phantom reads in reporting queries), I'd use **REPEATABLE READ**. `SERIALIZABLE` is overkill here — it would abort transactions on conflicts, requiring retry logic.

---

## Normalization

### Q: What normal form is your schema in?

**A:** Third Normal Form (3NF):
- **1NF**: Atomic columns, each row is unique (PK)
- **2NF**: No partial dependencies — all non-key columns depend on the full PK
- **3NF**: No transitive dependencies — `seat.train_id` is a FK, but `train.name` is not stored in the `seats` table

### Q: Why not store user name directly in the bookings table?

**A:** That would violate 3NF (transitive dependency: booking → user → name). If a user changes their name, you'd have to update every booking. With normalization, the name lives in one place — `users.name` — and bookings reference it via `user_id`.

### Q: Could you denormalize for performance?

**A:** Yes, if read-heavy queries join bookings with user names frequently, I could store `user_name` in `bookings` as a cache. This sacrifices write-safety for read speed. For this project, normalization is correct — the schema prioritizes data integrity over query optimization.

---

## Indexing

### Q: What indexes does your schema have and why?

**A:**
- **PK indexes** (auto): `users.id`, `trains.id`, `seats.id`, `bookings.id` — fast lookups by ID
- **Foreign key indexes**: PostgreSQL doesn't auto-index FKs, but `bookings.seat_id`, `bookings.user_id`, `seats.train_id` would benefit from indexes for join performance
- **Composite index**: A unique index on `(train_id, seat_number)` in `seats` prevents duplicate seat numbers per train

For a production system, I'd add:
```sql
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_expires ON bookings(expires_at) WHERE status = 'PENDING';
```

### Q: How does PostgreSQL's B-tree index work?

**A:** It stores key-value pairs in a balanced tree structure. Lookups, inserts, and deletes are O(log n). PostgreSQL's B-tree also supports multi-column indexes where the order of columns matters for query patterns.

---

## Locking & Concurrency

### Q: Pessimistic vs Optimistic locking — when to use which?

**A:**

| | Pessimistic Locking | Optimistic Locking |
|---|---|---|
| **How it works** | Lock the row (`SELECT FOR UPDATE`) — others wait | Read without lock, check version on write — retry on conflict |
| **When to use** | High contention, conflicts are expected | Low contention, conflicts are rare |
| **Booking system** | ✅ Correct choice — every seat reservation *will* contend for the same row | ❌ Would cause too many rollbacks/retries on popular seats |

### Q: How does `SELECT ... FOR UPDATE` prevent double-booking?

**A:**

```
Time │ Transaction A (User 1)          │ Transaction B (User 2)
─────┼─────────────────────────────────┼────────────────────────────────
  t1 │ BEGIN                           │ BEGIN
  t2 │ SELECT * FROM seats             │
     │ WHERE id = 1 FOR UPDATE         │
  t3 │ (holds lock)                    │ SELECT * FROM seats
     │                                 │ WHERE id = 1 FOR UPDATE
  t4 │                                 │ (BLOCKED — waits for A)
  t5 │ seat.is_available = True        │
     │ → book it                       │
  t6 │ COMMIT (lock released)          │
  t7 │                                 │ (acquires lock, reads row)
  t8 │                                 │ seat.is_available = False now
     │                                 │ → correctly refuses booking
  t9 │                                 │ ROLLBACK or continues
```

Transaction B cannot see stale data because FOR UPDATE blocks until A commits, then re-reads the fresh row.

### Q: What about deadlocks?

**A:** A deadlock occurs when Transaction A locks Seat 1 and waits for Seat 2, while Transaction B locks Seat 2 and waits for Seat 1. PostgreSQL detects this and aborts one transaction. To prevent it:
- Always lock resources in a consistent order (e.g., by seat ID ascending)
- Keep transaction duration short
- For bulk operations, acquire all locks upfront

### Q: Your expired hold mechanism — explain it.

**A:** When a seat is reserved, `expires_at` is set to `now + 5 minutes`. The `/admin/cleanup` endpoint (or a scheduled cron job) runs `SELECT ... FOR UPDATE` on all PENDING bookings where `expires_at < now()`, marks them CANCELLED, and sets `seats.is_available = True`. In production, I'd use `pg_cron` or a background worker.

---

## Transactions

### Q: What happens if the server crashes mid-transaction?

**A:** PostgreSQL's WAL (Write-Ahead Log) ensures durability. On restart, PostgreSQL replays WAL entries for committed transactions and discards uncommitted ones. The seat remains available because the transaction never committed.

### Q: Why does SQLAlchemy's `with_for_update()` map to `SELECT ... FOR UPDATE`?

**A:** SQLAlchemy's dialect system converts ORM operations to database-specific SQL. For PostgreSQL, `.with_for_update()` generates `SELECT ... FOR UPDATE`. For MySQL, it would generate the same. For SQLite (which lacks row-level locking), it would either be ignored or raise an error depending on the version.

---

## SQL

### Q: Write a query to find all available seats on a train with their prices.

**A:**
```sql
SELECT s.id, s.seat_number, t.base_price
FROM seats s
JOIN trains t ON s.train_id = t.id
WHERE s.train_id = 1 AND s.is_available = true
ORDER BY s.seat_number;
```

### Q: Find the user who has made the most bookings.

**A:**
```sql
SELECT u.name, u.email, COUNT(b.id) as booking_count
FROM users u
JOIN bookings b ON u.id = b.user_id
GROUP BY u.id, u.name, u.email
ORDER BY booking_count DESC
LIMIT 1;
```

### Q: Find seats that were booked but never confirmed (abandoned holds).

**A:**
```sql
SELECT s.seat_number, b.created_at, b.expires_at
FROM bookings b
JOIN seats s ON b.seat_id = s.id
WHERE b.status = 'CANCELLED'
  AND b.expires_at IS NOT NULL
  AND b.expires_at < NOW();
```

---

## Database Design

### Q: Why PostgreSQL over MongoDB for this project?

**A:** Booking engines require ACID compliance to prevent double-booking. PostgreSQL provides row-level locks, foreign key constraints, and transaction isolation — all critical for inventory reservations. MongoDB (pre-4.0) lacked multi-document ACID transactions. Even with 4.0+, document databases trade strict consistency for horizontal scaling, which isn't needed here.

### Q: How would you scale this database?

**A:**
- **Read replicas**: Offload `GET /trains` and `GET /seats` queries to replicas
- **Connection pooling**: Use PgBouncer to manage a large number of concurrent connections
- **Partitioning**: Partition `bookings` by `created_at` (range partitioning by month) for faster archival queries
- **Caching**: Cache train and seat availability in Redis for read-heavy workloads
