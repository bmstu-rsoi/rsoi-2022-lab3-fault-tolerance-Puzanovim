from typing import Awaitable
from uuid import UUID

from httpx import AsyncClient, Response

from gateway_service.apis.library_system_api.schemas import (
    BookModel,
    BooksPagination,
    LibrariesPagination,
    LibraryModel,
)
from gateway_service.circuit_breaker import CircuitBreaker
from gateway_service.config import LIBRARY_SYSTEM_CONFIG
from gateway_service.exceptions import ServiceNotAvailableError
from gateway_service.validators import json_dump


class LibrarySystemAPI:
    def __init__(self, host: str = LIBRARY_SYSTEM_CONFIG.host, port: int = LIBRARY_SYSTEM_CONFIG.port) -> None:
        self._host = host
        self._port = port

        self._circuit_breaker: CircuitBreaker = CircuitBreaker(name=self.__class__.__name__)

    async def get_libraries(self, city: str, page: int, size: int) -> LibrariesPagination | None:
        params = {'city': city, 'page': page, 'size': size}
        async with AsyncClient() as client:
            func: Awaitable = client.get(f'http://{self._host}:{self._port}/libraries', params=params)
            response: Response | None = await self._circuit_breaker.request(func)

        if response is not None:
            return LibrariesPagination(**response.json())
        return None

    async def get_library(self, library_uid: UUID) -> LibraryModel:
        library: LibraryModel

        async with AsyncClient() as client:
            func = client.get(f'http://{self._host}:{self._port}/libraries/{library_uid}')
            response: Response | None = await self._circuit_breaker.request(func)

        if response is not None:
            library = LibraryModel(**response.json())
        else:
            library = LibraryModel(libraryUid=library_uid)

        return library

    async def get_books(self, library_uid: UUID, page: int, size: int, show_all: bool) -> BooksPagination | None:
        params = {'page': page, 'size': size, 'show_all': show_all}
        async with AsyncClient() as client:
            func = client.get(f'http://{self._host}:{self._port}/libraries/{library_uid}/books', params=params)
            response: Response | None = await self._circuit_breaker.request(func)

        if response is not None:
            return BooksPagination(**response.json())
        return None

    async def get_book(self, library_uid: UUID, book_uid: UUID) -> BookModel:
        book: BookModel

        async with AsyncClient() as client:
            func = client.get(f'http://{self._host}:{self._port}/libraries/{library_uid}/books/{book_uid}')
            response: Response | None = await self._circuit_breaker.request(func)

        if response is not None:
            book = BookModel(**response.json())
        else:
            book = BookModel(bookUid=book_uid)

        return book

    async def reserve_book(self, library_uid: UUID, book_uid: UUID) -> None:
        body = json_dump({'library_uid': library_uid, 'book_uid': book_uid})
        async with AsyncClient() as client:
            func = client.post(
                f'http://{self._host}:{self._port}/libraries/{library_uid}/books/{book_uid}/reserve',
                json=body,
            )
            response: Response | None = await self._circuit_breaker.request(func)

        if response is None or response.status_code != 200:
            raise ServiceNotAvailableError
        return None

    async def return_book(self, library_uid: UUID, book_uid: UUID) -> None:
        body = json_dump({'library_uid': library_uid, 'book_uid': book_uid})
        async with AsyncClient() as client:
            func = client.post(
                f'http://{self._host}:{self._port}/libraries/{library_uid}/books/{book_uid}/return',
                json=body,
            )
            response: Response | None = await self._circuit_breaker.request(func)

        if response is None or response.status_code != 200:
            raise ServiceNotAvailableError
        return None
