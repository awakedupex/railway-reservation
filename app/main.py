from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.services.booking import BookingService
from app.schemas import ReserveRequest, ConfirmRequest, BookingResponse
from app.models import Train, Seat, User

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Railway Reservation System")


@app.get("/")
def root():
    return {"service": "Railway Reservation System", "status": "running"}


@app.get("/trains")
def list_trains(db: Session = Depends(get_db)):
    trains = db.query(Train).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "source": t.source,
            "destination": t.destination,
            "base_price": t.base_price,
        }
        for t in trains
    ]


@app.get("/trains/{train_id}/seats")
def list_seats(train_id: int, db: Session = Depends(get_db)):
    seats = db.query(Seat).filter(Seat.train_id == train_id).all()
    return [
        {
            "id": s.id,
            "seat_number": s.seat_number,
            "is_available": s.is_available,
        }
        for s in seats
    ]


@app.post("/bookings/reserve", response_model=BookingResponse)
def reserve_seat(req: ReserveRequest, db: Session = Depends(get_db)):
    service = BookingService(db)
    try:
        result = service.reserve_seat(req.seat_id, req.user_id, req.user_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/bookings/confirm", response_model=BookingResponse)
def confirm_booking(req: ConfirmRequest, db: Session = Depends(get_db)):
    service = BookingService(db)
    try:
        result = service.confirm_booking(req.booking_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/bookings/cancel", response_model=BookingResponse)
def cancel_booking(req: ConfirmRequest, db: Session = Depends(get_db)):
    service = BookingService(db)
    try:
        result = service.cancel_booking(req.booking_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/admin/cleanup")
def cleanup_expired(db: Session = Depends(get_db)):
    service = BookingService(db)
    count = service.cleanup_expired_holds()
    return {"released_holds": count}
