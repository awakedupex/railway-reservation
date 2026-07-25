from abc import ABC, abstractmethod


class BookingState(ABC):
    @abstractmethod
    def confirm(self) -> str:
        pass

    @abstractmethod
    def cancel(self) -> str:
        pass


class PendingState(BookingState):
    def confirm(self) -> str:
        return "CONFIRMED"

    def cancel(self) -> str:
        return "CANCELLED"


class ConfirmedState(BookingState):
    def confirm(self) -> str:
        raise ValueError("Booking is already confirmed")

    def cancel(self) -> str:
        return "CANCELLED"


class CancelledState(BookingState):
    def confirm(self) -> str:
        raise ValueError("Cannot confirm a cancelled booking")

    def cancel(self) -> str:
        raise ValueError("Booking is already cancelled")


def get_state(status: str) -> BookingState:
    mapping = {
        "PENDING": PendingState(),
        "CONFIRMED": ConfirmedState(),
        "CANCELLED": CancelledState(),
    }
    state = mapping.get(status)
    if not state:
        raise ValueError(f"Unknown booking status: {status}")
    return state
