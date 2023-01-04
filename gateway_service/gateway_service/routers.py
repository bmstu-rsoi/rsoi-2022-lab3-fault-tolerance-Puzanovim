import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from gateway_service.apis import (
    LibrarySystemAPI,
    RatingSystemAPI,
    ReservationSystemAPI,
    get_library_system_api,
    get_rating_system_api,
    get_reservation_system_api,
)
from gateway_service.apis.library_system_api.schemas import BookModel, BooksPagination, LibrariesPagination
from gateway_service.apis.rating_system_api.schemas import UserRating
from gateway_service.apis.reservation_system.schemas import (
    RentedBooks,
    ReservationBookInput,
    ReservationBookResponse,
    ReservationModel,
    ReservationResponse,
    ReservationUpdate,
    ReturnBookInput,
    Status,
)
from gateway_service.validators import validate_page_size_params

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    '/libraries',
    status_code=status.HTTP_200_OK,
    response_model=LibrariesPagination,
    summary='Получить список библиотек в городе',
)
async def get_libraries(
    city: str, page: int = 0, size: int = 100, library_system_api: LibrarySystemAPI = Depends(get_library_system_api)
) -> LibrariesPagination:
    validate_page_size_params(page, size)
    libraries: LibrariesPagination = await library_system_api.get_libraries(city, page, size)
    return libraries


@router.get(
    '/libraries/{library_uid}/books',
    status_code=status.HTTP_200_OK,
    response_model=BooksPagination,
    summary='Получить список книг в выбранной библиотеке',
)
async def get_books(
    library_uid: UUID,
    page: int = 0,
    size: int = 100,
    show_all: bool = False,
    library_system_api: LibrarySystemAPI = Depends(get_library_system_api),
) -> BooksPagination:
    validate_page_size_params(page, size)
    books: BooksPagination = await library_system_api.get_books(library_uid, page, size, show_all)
    return books


@router.get(
    '/reservations',
    status_code=status.HTTP_200_OK,
    response_model=List[ReservationResponse],
    summary='Получить информацию по всем взятым в прокат книгам пользователя',
)
async def get_reservations(
    x_user_name: str = Header(),
    reservation_system_api: ReservationSystemAPI = Depends(get_reservation_system_api),
    library_system_api: LibrarySystemAPI = Depends(get_library_system_api),
) -> List[ReservationResponse]:
    reservations: List[ReservationModel] = await reservation_system_api.get_reservations(x_user_name)
    print(f'RESERVATIONS: {reservations}')
    return [
        ReservationResponse(
            **reservation.dict(exclude={'library_uid', 'book_uid'}),
            book=(await library_system_api.get_book(reservation.libraryUid, reservation.bookUid)),
            library=(await library_system_api.get_library(reservation.libraryUid)),
        )
        for reservation in reservations
    ]


@router.post(
    '/reservations',
    status_code=status.HTTP_200_OK,
    response_model=ReservationBookResponse,
    summary='Взять книгу в библиотеке',
)
async def reserve_book(
    reservation_book_input: ReservationBookInput,
    x_user_name: str = Header(),
    reservation_system_api: ReservationSystemAPI = Depends(get_reservation_system_api),
    rating_system_api: RatingSystemAPI = Depends(get_rating_system_api),
    library_system_api: LibrarySystemAPI = Depends(get_library_system_api),
) -> ReservationBookResponse:
    rented_books: RentedBooks = await reservation_system_api.get_count_rented_books(x_user_name)
    user_rating: UserRating = await rating_system_api.get_rating(x_user_name)

    if rented_books.count >= user_rating.stars:
        raise PermissionError

    reservation: ReservationModel = await reservation_system_api.reserve_book(x_user_name, reservation_book_input)
    await library_system_api.reserve_book(reservation_book_input.libraryUid, reservation_book_input.bookUid)
    # except Exception: raise status=400 ERROR(message: str, errors: List[Error(field: str, error: str)])

    return ReservationBookResponse(
        **reservation.dict(exclude={'bookUid', 'libraryUid'}),
        book=(await library_system_api.get_book(reservation.libraryUid, reservation.bookUid)),
        library=(await library_system_api.get_library(reservation.libraryUid)),
        rating=user_rating,
    )


@router.post('/reservations/{reservation_uid}/return', status_code=status.HTTP_204_NO_CONTENT, summary='Вернуть книгу')
async def return_book(
    reservation_uid: UUID,
    return_book_input: ReturnBookInput,
    x_user_name: str = Header(),
    reservation_system_api: ReservationSystemAPI = Depends(get_reservation_system_api),
    library_system_api: LibrarySystemAPI = Depends(get_library_system_api),
    rating_system_api: RatingSystemAPI = Depends(get_rating_system_api)
) -> None:
    reservation: ReservationModel = await reservation_system_api.get_reservation(x_user_name, reservation_uid)
    book: BookModel = await library_system_api.get_book(reservation.libraryUid, reservation.bookUid)

    change_stars = 0
    if book.condition != return_book_input.condition:
        change_stars -= 10

    if return_book_input.date > reservation.tillDate:
        return_status = Status.EXPIRED
        change_stars -= 10
    else:
        return_status = Status.RETURNED
    reservation_update = ReservationUpdate(status=return_status)
    change_stars = change_stars if change_stars else 1

    await library_system_api.return_book(reservation.libraryUid, reservation.bookUid)
    await reservation_system_api.return_book(x_user_name, reservation_uid, reservation_update)
    await rating_system_api.update_rating(x_user_name, change_stars)
    # ERROR status_code=404 Error(message: str)


@router.get('/rating', status_code=status.HTTP_200_OK, summary='Получить рейтинг пользователя')
async def get_rating(
    x_user_name: str = Header(), rating_system_api: RatingSystemAPI = Depends(get_rating_system_api)
) -> UserRating:
    user_rating: UserRating = await rating_system_api.get_rating(x_user_name)
    return user_rating
