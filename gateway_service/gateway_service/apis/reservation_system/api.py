import json
from typing import Dict, List
from uuid import UUID

from gateway_service.apis.reservation_system.schemas import (
    RentedBooks,
    ReservationBookInput,
    ReservationModel,
    ReservationUpdate,
)
from gateway_service.config import RESERVATION_SYSTEM_CONFIG
from gateway_service.validators import json_dump
from httpx import AsyncClient


class ReservationSystemAPI:
    def __init__(self, host: str = RESERVATION_SYSTEM_CONFIG.host, port: int = RESERVATION_SYSTEM_CONFIG.port) -> None:
        self._host = host
        self._port = port

    async def get_reservations(self, username: str) -> List[ReservationModel]:
        headers = {'X-User-Name': username}
        async with AsyncClient() as client:
            response = await client.get(f'http://{self._host}:{self._port}/reservations', headers=headers)

        if response.status_code != 200:
            print(response.json())

        dict_reservations: List[Dict] = response.json()
        reservations: List[ReservationModel] = [ReservationModel(**reservation) for reservation in dict_reservations]
        return reservations

    async def get_reservation(self, username: str, reservation_uid: UUID) -> ReservationModel:
        headers = {'X-User-Name': username}
        async with AsyncClient() as client:
            response = await client.get(
                f'http://{self._host}:{self._port}/reservations/{reservation_uid}', headers=headers
            )

        if response.status_code != 200:
            print(response.json())

        reservation_book: ReservationModel = ReservationModel(**response.json())
        return reservation_book

    async def get_count_rented_books(self, username: str) -> RentedBooks:
        headers = {'X-User-Name': username}
        async with AsyncClient() as client:
            response = await client.get(f'http://{self._host}:{self._port}/rented', headers=headers)

        if response.status_code != 200:
            print(response.json())

        return RentedBooks(**response.json())

    async def reserve_book(self, username: str, reservation_book_input: ReservationBookInput) -> ReservationModel:
        headers = {'X-User-Name': username}
        body: Dict = json_dump(reservation_book_input.dict())
        async with AsyncClient() as client:
            response = await client.post(
                f'http://{self._host}:{self._port}/reservations', headers=headers, json=body
            )

        if response.status_code != 200:
            print(response.json())

        reservation_book: ReservationModel = ReservationModel(**response.json())
        return reservation_book

    async def return_book(self, username: str, reservation_uid: UUID, reservation_update: ReservationUpdate) -> None:
        headers = {'X-User-Name': username}
        body = json_dump(reservation_update.dict())
        async with AsyncClient() as client:
            response = await client.post(
                f'http://{self._host}:{self._port}/reservations/{reservation_uid}/return',
                headers=headers,
                json=body,
            )

        if response.status_code != 200:
            print(response.json())

        if response.status_code == 204:
            return None
        elif response.status_code == 404:
            pass
            # return ErrorResponse(**response.json())
