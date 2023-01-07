from httpx import AsyncClient, Response

from gateway_service.apis.rating_system_api.schemas import UserRating
from gateway_service.circuit_breaker import CircuitBreaker
from gateway_service.config import RATING_SYSTEM_CONFIG
from gateway_service.exceptions import ServiceNotAvailableError
from gateway_service.validators import json_dump


class RatingSystemAPI:
    def __init__(self, host: str = RATING_SYSTEM_CONFIG.host, port: int = RATING_SYSTEM_CONFIG.port) -> None:
        self._host = host
        self._port = port

        self._circuit_breaker: CircuitBreaker = CircuitBreaker(name=self.__class__.__name__)

    async def get_rating(self, username: str) -> UserRating | None:
        headers = {'X-User-Name': username}
        async with AsyncClient() as client:
            func = client.get(f'http://{self._host}:{self._port}/rating', headers=headers)
            response: Response | None = await self._circuit_breaker.request(func)

        if response is not None:
            return UserRating(**response.json())
        else:
            return None

    async def update_rating(self, username: str, new_stars: int) -> UserRating | None:
        headers = {'X-User-Name': username}
        body = json_dump(UserRating(stars=new_stars).dict())
        async with AsyncClient() as client:
            func = client.post(f'http://{self._host}:{self._port}/rating', headers=headers, json=body)
            response: Response | None = await self._circuit_breaker.request(func)

        if response is not None:
            return UserRating(**response.json())
        else:
            raise ServiceNotAvailableError
