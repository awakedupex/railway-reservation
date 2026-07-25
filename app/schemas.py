from pydantic import BaseModel
from typing import Optional


class ReserveRequest(BaseModel):
    seat_id: int
    user_id: int
    user_type: str = "standard"


class ConfirmRequest(BaseModel):
    booking_id: int


class CancelRequest(BaseModel):
    booking_id: int


class BookingResponse(BaseModel):
    booking_id: int
    status: str
    price: Optional[float] = None
    message: Optional[str] = None
