import logging
from asyncio import Queue
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response, status

from gateway_service.apis import (
    LibrarySystemAPI,
    RatingSystemAPI,
    ReservationSystemAPI,
    get_library_system_api,
    get_rating_system_api,
    get_reservation_system_api,
)
from gateway_service.apis.library_system_api.schemas import BookModel, BooksPagination, Condition, LibrariesPagination
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
from gateway_service.exceptions import ServiceNotAvailableError, ServiceTemporaryNotAvailableError
from gateway_service.queue_processor import Func, get_queue
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
    libraries: LibrariesPagination | None = await library_system_api.get_libraries(city, page, size)

    if libraries is None:
        raise ServiceNotAvailableError

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
    books: BooksPagination | None = await library_system_api.get_books(library_uid, page, size, show_all)

    if books is None:
        raise ServiceNotAvailableError

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
    reservations: List[ReservationModel] | None = await reservation_system_api.get_reservations(x_user_name)

    if reservations is None:
        raise ServiceNotAvailableError

    return [
        ReservationResponse(
            **reservation.dict(exclude={'library_uid', 'book_uid'}),
            book=(await library_system_api.get_book(reservation.libraryUid, reservation.bookUid)),
            library=(await library_system_api.get_library(reservation.libraryUid)),
        )
        for reservation in reservations
    ]


async def _reserve_book(
    reservation_book_input: ReservationBookInput,
    x_user_name: str = Header(),
    reservation_system_api: ReservationSystemAPI = Depends(get_reservation_system_api),
    rating_system_api: RatingSystemAPI = Depends(get_rating_system_api),
    library_system_api: LibrarySystemAPI = Depends(get_library_system_api),
) -> ReservationBookResponse:
    rented_books: RentedBooks | None = await reservation_system_api.get_count_rented_books(x_user_name)
    user_rating: UserRating | None = await rating_system_api.get_rating(x_user_name)

    if rented_books is None or user_rating is None:
        logger.info(f'RESERVING BOOK: raising ServiceNotAvailableError')
        raise ServiceNotAvailableError

    if rented_books.count >= user_rating.stars:
        logger.info(f'RESERVING BOOK: raising PermissionError')
        raise PermissionError

    try:
        reservation: ReservationModel = await reservation_system_api.reserve_book(x_user_name, reservation_book_input)
    except ServiceNotAvailableError:
        logger.info(f'RESERVING BOOK: raising ServiceTemporaryNotAvailableError 1 step')
        raise ServiceTemporaryNotAvailableError

    try:
        await library_system_api.reserve_book(reservation.libraryUid, reservation.bookUid)
    except ServiceNotAvailableError:
        await reservation_system_api.delete_reserve(x_user_name, reservation.reservationUid)
        logger.info(f'RESERVING BOOK: raising ServiceTemporaryNotAvailableError 2 step')
        raise ServiceTemporaryNotAvailableError

    logger.info(f'RESERVING BOOK: all done')

    return ReservationBookResponse(
        **reservation.dict(exclude={'bookUid', 'libraryUid'}),
        book=(await library_system_api.get_book(reservation.libraryUid, reservation.bookUid)),
        library=(await library_system_api.get_library(reservation.libraryUid)),
        rating=user_rating,
    )


@router.post(
    '/reservations',
    status_code=status.HTTP_200_OK,
    response_model=ReservationBookResponse,
    summary='Взять книгу в библиотеке',
)
async def reserve_book_handler(
    reservation_book_input: ReservationBookInput,
    x_user_name: str = Header(),
    reservation_system_api: ReservationSystemAPI = Depends(get_reservation_system_api),
    rating_system_api: RatingSystemAPI = Depends(get_rating_system_api),
    library_system_api: LibrarySystemAPI = Depends(get_library_system_api),
    queue: Queue = Depends(get_queue),
) -> ReservationBookResponse | Response:
    func_name = _reserve_book
    func_args = (
        reservation_book_input, x_user_name, reservation_system_api, rating_system_api, library_system_api
    )

    logger.info(f'QUEUE SIZE RESERVING BOOK before: {queue.qsize()}')
    try:
        reservation_response: ReservationBookResponse = await func_name(*func_args)
    except ServiceTemporaryNotAvailableError:
        logger.info(f'RESERVING BOOK: catch ServiceTemporaryNotAvailableError')
        await queue.put(Func(name=func_name, args=func_args))
        logger.info(f'QUEUE SIZE RESERVING BOOK after: {queue.qsize()}')
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    logger.info(f'QUEUE SIZE RESERVING BOOK after: {queue.qsize()}')
    return reservation_response


async def _return_book(
    reservation_uid: UUID,
    return_book_input: ReturnBookInput,
    x_user_name: str = Header(),
    reservation_system_api: ReservationSystemAPI = Depends(get_reservation_system_api),
    library_system_api: LibrarySystemAPI = Depends(get_library_system_api),
    rating_system_api: RatingSystemAPI = Depends(get_rating_system_api),
) -> None:
    reservation: ReservationModel | None = await reservation_system_api.get_reservation(x_user_name, reservation_uid)
    book: BookModel = await library_system_api.get_book(reservation.libraryUid, reservation.bookUid)

    if reservation is None or book.condition == Condition.UNKNOWN:
        logger.info(f'RETURNING BOOK: raising ServiceNotAvailableError')
        raise ServiceNotAvailableError

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

    try:
        await library_system_api.return_book(reservation.libraryUid, reservation.bookUid)
    except ServiceNotAvailableError:
        logger.info(f'RETURNING BOOK: raising ServiceTemporaryNotAvailableError 1 step')
        raise ServiceTemporaryNotAvailableError

    try:
        await reservation_system_api.return_book(x_user_name, reservation_uid, reservation_update)
    except ServiceNotAvailableError:
        await library_system_api.reserve_book(reservation.libraryUid, reservation.bookUid)
        logger.info(f'RETURNING BOOK: raising ServiceTemporaryNotAvailableError 2 step')
        raise ServiceTemporaryNotAvailableError

    try:
        await rating_system_api.update_rating(x_user_name, change_stars)
    except ServiceNotAvailableError:
        undo_reservation_update = ReservationUpdate(status=Status.RENTED)
        await reservation_system_api.return_book(x_user_name, reservation_uid, undo_reservation_update)
        await library_system_api.reserve_book(reservation.libraryUid, reservation.bookUid)
        logger.info(f'RETURNING BOOK: raising ServiceTemporaryNotAvailableError 3 step')
        raise ServiceTemporaryNotAvailableError

    logger.info(f'RETURNING BOOK: all done')


@router.post('/reservations/{reservation_uid}/return', status_code=status.HTTP_204_NO_CONTENT, summary='Вернуть книгу')
async def return_book_handler(
    reservation_uid: UUID,
    return_book_input: ReturnBookInput,
    x_user_name: str = Header(),
    reservation_system_api: ReservationSystemAPI = Depends(get_reservation_system_api),
    library_system_api: LibrarySystemAPI = Depends(get_library_system_api),
    rating_system_api: RatingSystemAPI = Depends(get_rating_system_api),
    queue: Queue = Depends(get_queue),
) -> None:
    func_name = _return_book
    func_args = (
        reservation_uid, return_book_input, x_user_name, reservation_system_api, library_system_api, rating_system_api
    )

    logger.info(f'QUEUE SIZE RETURNING BOOK before: {queue.qsize()}')
    try:
        await func_name(*func_args)
    except ServiceTemporaryNotAvailableError:
        logger.info(f'RETURNING BOOK: catch ServiceTemporaryNotAvailableError')
        await queue.put(Func(name=func_name, args=func_args))

    logger.info(f'QUEUE SIZE RETURNING BOOK after: {queue.qsize()}')
    return None


@router.get('/rating', status_code=status.HTTP_200_OK, summary='Получить рейтинг пользователя')
async def get_rating(
    x_user_name: str = Header(), rating_system_api: RatingSystemAPI = Depends(get_rating_system_api)
) -> UserRating:
    user_rating: UserRating | None = await rating_system_api.get_rating(x_user_name)

    if user_rating is None:
        raise ServiceNotAvailableError

    return user_rating
