from typing import Dict, List
from uuid import UUID

from httpx import AsyncClient, Response

from gateway_service.apis.reservation_system.schemas import (
    RentedBooks,
    ReservationBookInput,
    ReservationModel,
    ReservationUpdate,
)
from gateway_service.circuit_breaker import CircuitBreaker
from gateway_service.config import RESERVATION_SYSTEM_CONFIG
from gateway_service.exceptions import ServiceNotAvailableError
from gateway_service.validators import json_dump


class ReservationSystemAPI:
    def __init__(self, host: str = RESERVATION_SYSTEM_CONFIG.host, port: int = RESERVATION_SYSTEM_CONFIG.port) -> None:
        self._host = host
        self._port = port

        self._circuit_breaker: CircuitBreaker = CircuitBreaker(name=self.__class__.__name__)

    async def get_reservations(self, username: str) -> List[ReservationModel] | None:
        headers = {'X-User-Name': username}
        async with AsyncClient() as client:
            func = client.get(f'http://{self._host}:{self._port}/reservations', headers=headers)
            response: Response | None = await self._circuit_breaker.request(func)

        if response is not None:
            dict_reservations: List[Dict] = response.json()
            reservations: List[ReservationModel] = [
                ReservationModel(**reservation) for reservation in dict_reservations
            ]
            return reservations
        return None

    async def get_reservation(self, username: str, reservation_uid: UUID) -> ReservationModel | None:
        headers = {'X-User-Name': username}
        async with AsyncClient() as client:
            func = client.get(f'http://{self._host}:{self._port}/reservations/{reservation_uid}', headers=headers)
            response: Response | None = await self._circuit_breaker.request(func)

        if response is not None:
            return ReservationModel(**response.json())
        return None

    async def get_count_rented_books(self, username: str) -> RentedBooks | None:
        headers = {'X-User-Name': username}
        async with AsyncClient() as client:
            func = client.get(f'http://{self._host}:{self._port}/rented', headers=headers)
            response: Response | None = await self._circuit_breaker.request(func)

        if response is not None:
            return RentedBooks(**response.json())
        return None

    async def reserve_book(self, username: str, reservation_book_input: ReservationBookInput) -> ReservationModel:
        headers = {'X-User-Name': username}
        body: Dict = json_dump(reservation_book_input.dict())
        async with AsyncClient() as client:
            func = client.post(f'http://{self._host}:{self._port}/reservations', headers=headers, json=body)
            response: Response | None = await self._circuit_breaker.request(func)

        if response is None:
            raise ServiceNotAvailableError

        reservation_book: ReservationModel = ReservationModel(**response.json())
        return reservation_book

    async def return_book(self, username: str, reservation_uid: UUID, reservation_update: ReservationUpdate) -> None:
        headers = {'X-User-Name': username}
        body = json_dump(reservation_update.dict())
        async with AsyncClient() as client:
            func = client.post(
                f'http://{self._host}:{self._port}/reservations/{reservation_uid}/return', headers=headers, json=body,
            )
            response: Response | None = await self._circuit_breaker.request(func)

        if response is None or response.status_code != 204:
            raise ServiceNotAvailableError
        return None

    async def delete_reserve(self, username: str, reservation_uid: UUID) -> None:
        headers = {'X-User-Name': username}
        async with AsyncClient() as client:
            func = client.delete(
                f'http://{self._host}:{self._port}/reservations/{reservation_uid}', headers=headers,
            )
            response: Response | None = await self._circuit_breaker.request(func)

        if response is None:
            raise ServiceNotAvailableError
        return None
