from sqlalchemy.orm import Session
from app.models import Booking, Seat, Train
from app.patterns.state import get_state
from app.patterns.strategy import PricingContext, StandardPricing, StudentDiscountPricing, SeniorCitizenPricing
from datetime import datetime, timedelta


USER_TYPE_STRATEGY = {
    "standard": StandardPricing(),
    "student": StudentDiscountPricing(),
    "senior": SeniorCitizenPricing(),
}


class BookingService:
    def __init__(self, db: Session):
        self.db = db

    def reserve_seat(self, seat_id: int, user_id: int, user_type: str = "standard"):
        seat = self.db.query(Seat).filter(Seat.id == seat_id).with_for_update().first()

        if not seat:
            raise ValueError("Seat not found")
        if not seat.is_available:
            raise ValueError("Seat is already booked")

        train = self.db.query(Train).filter(Train.id == seat.train_id).first()

        strategy = USER_TYPE_STRATEGY.get(user_type, StandardPricing())
        context = PricingContext(strategy)
        final_price = context.get_price(train.base_price)

        booking = Booking(
            seat_id=seat_id,
            user_id=user_id,
            status="PENDING",
            price=final_price,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )
        seat.is_available = False
        self.db.add(booking)
        self.db.commit()

        return {"booking_id": booking.id, "price": final_price, "status": "PENDING"}

    def confirm_booking(self, booking_id: int):
        booking = self.db.query(Booking).filter(Booking.id == booking_id).with_for_update().first()
        if not booking:
            raise ValueError("Booking not found")

        state = get_state(booking.status)
        new_status = state.confirm()
        booking.status = new_status
        booking.expires_at = None
        self.db.commit()

        return {"booking_id": booking.id, "status": new_status, "message": "Booking confirmed"}

    def cancel_booking(self, booking_id: int):
        booking = self.db.query(Booking).filter(Booking.id == booking_id).with_for_update().first()
        if not booking:
            raise ValueError("Booking not found")

        state = get_state(booking.status)
        new_status = state.cancel()
        booking.status = new_status

        seat = self.db.query(Seat).filter(Seat.id == booking.seat_id).first()
        if seat:
            seat.is_available = True

        self.db.commit()

        return {"booking_id": booking.id, "status": new_status, "message": "Booking cancelled"}

    def cleanup_expired_holds(self):
        expired = (
            self.db.query(Booking)
            .filter(
                Booking.status == "PENDING",
                Booking.expires_at < datetime.utcnow(),
            )
            .with_for_update()
            .all()
        )

        for booking in expired:
            seat = self.db.query(Seat).filter(Seat.id == booking.seat_id).first()
            if seat:
                seat.is_available = True
            booking.status = "CANCELLED"

        self.db.commit()
        return len(expired)
