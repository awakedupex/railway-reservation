import os
from dotenv import load_dotenv

load_dotenv()

from app.database import engine, Base, SessionLocal
from app.models import User, Train, Seat

Base.metadata.create_all(bind=engine)

db = SessionLocal()

if db.query(Train).count() > 0:
    print("Database already seeded. Skipping.")
    db.close()
    exit(0)

users = [
    User(name="Alice", email="alice@example.com"),
    User(name="Bob", email="bob@example.com"),
    User(name="Charlie", email="charlie@example.com"),
]
db.add_all(users)
db.flush()

train = Train(name="Shatabdi Express", source="Mumbai", destination="Delhi", base_price=1200.0)
db.add(train)
db.flush()

for i in range(1, 41):
    seat = Seat(train_id=train.id, seat_number=f"A{i:02d}", is_available=True)
    db.add(seat)

train2 = Train(name="Rajdhani Express", source="Delhi", destination="Bangalore", base_price=2400.0)
db.add(train2)
db.flush()

for i in range(1, 31):
    seat = Seat(train_id=train2.id, seat_number=f"B{i:02d}", is_available=True)
    db.add(seat)

db.commit()
db.close()
print("Database seeded successfully with 2 trains, 70 seats, and 3 users!")
