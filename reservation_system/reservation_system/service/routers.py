from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from reservation_system.db.repository import ReservationRepository, get_reservation_repository
from reservation_system.service.schemas import (
    RentedBooks,
    ReservationInput,
    ReservationModel,
    ReservationRequest,
    ReservationResponse,
    ReservationUpdate,
)

router = APIRouter()


@router.get('/reservations', status_code=status.HTTP_200_OK, response_model=List[ReservationResponse])
async def get_reservations(
    x_user_name: str = Header(), repository: ReservationRepository = Depends(get_reservation_repository)
) -> List[ReservationResponse]:
    reservations: List[ReservationModel] = await repository.get_reservations(x_user_name)
    reservations_response: List[ReservationResponse] = [
        ReservationResponse(
            **reservation.dict(exclude={'id', 'reservation_uid', 'book_uid', 'library_uid', 'start_date', 'till_date'}),
            reservationUid=reservation.reservation_uid,
            bookUid=reservation.book_uid,
            libraryUid=reservation.library_uid,
            startDate=reservation.start_date,
            tillDate=reservation.till_date,
        )
        for reservation in reservations
    ]
    return reservations_response


@router.get('/reservations/{reservation_uid}', status_code=status.HTTP_200_OK, response_model=ReservationResponse)
async def get_reservation(
    reservation_uid: UUID, repository: ReservationRepository = Depends(get_reservation_repository)
) -> ReservationResponse:
    reservation: ReservationModel = await repository.get_reservation(reservation_uid)
    return ReservationResponse(
        **reservation.dict(exclude={'id', 'reservation_uid', 'book_uid', 'library_uid', 'start_date', 'till_date'}),
        reservationUid=reservation.reservation_uid,
        bookUid=reservation.book_uid,
        libraryUid=reservation.library_uid,
        startDate=reservation.start_date,
        tillDate=reservation.till_date,
    )


@router.post('/reservations', status_code=status.HTTP_201_CREATED, response_model=ReservationResponse)
async def create_reservation(
    reservation_request: ReservationRequest,
    x_user_name: str = Header(),
    repository: ReservationRepository = Depends(get_reservation_repository),
) -> ReservationResponse:
    reservation_input: ReservationInput = ReservationInput(
        book_uid=reservation_request.bookUid,
        library_uid=reservation_request.libraryUid,
        till_date=reservation_request.tillDate,
        username=x_user_name
    )
    reservation: ReservationModel = await repository.create_reservation(reservation_input)
    return ReservationResponse(
        **reservation.dict(exclude={'id', 'reservation_uid', 'book_uid', 'library_uid', 'start_date', 'till_date'}),
        reservationUid=reservation.reservation_uid,
        bookUid=reservation.book_uid,
        libraryUid=reservation.library_uid,
        startDate=reservation.start_date,
        tillDate=reservation.till_date,
    )


@router.delete('/reservations/{reservation_uid}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(
    reservation_uid: UUID,
    x_user_name: str = Header(),
    repository: ReservationRepository = Depends(get_reservation_repository),
) -> None:
    await repository.delete_reservation(reservation_uid, x_user_name)


@router.post('/reservations/{reservation_uid}/return', status_code=status.HTTP_204_NO_CONTENT)
async def return_book(
    reservation_uid: UUID,
    reservation_request: ReservationUpdate,
    x_user_name: str = Header(),
    repository: ReservationRepository = Depends(get_reservation_repository),
) -> None:
    await repository.update_reservation(reservation_uid, x_user_name, reservation_request)


@router.get('/rented', status_code=status.HTTP_200_OK, response_model=RentedBooks)
async def get_rented_books(
    x_user_name: str = Header(), repository: ReservationRepository = Depends(get_reservation_repository)
) -> RentedBooks:
    rented_books: RentedBooks = await repository.get_rented_books(x_user_name)
    return rented_books
