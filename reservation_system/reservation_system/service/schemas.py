from datetime import date
from uuid import UUID

from pydantic import BaseModel
from reservation_system.db.models import Status


class ReservationRequest(BaseModel):
    bookUid: UUID
    libraryUid: UUID
    tillDate: date


class ReservationBase(BaseModel):
    username: str
    status: Status = Status.RENTED

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class ReservationInput(ReservationBase):
    book_uid: UUID
    library_uid: UUID
    start_date: date = date.today()
    till_date: date


class ReservationModel(ReservationInput):
    id: int
    reservation_uid: UUID


class ReservationUpdate(BaseModel):
    status: Status


class ReservationResponse(ReservationBase):
    reservationUid: UUID
    bookUid: UUID
    libraryUid: UUID
    startDate: date
    tillDate: date


class RentedBooks(BaseModel):
    count: int
