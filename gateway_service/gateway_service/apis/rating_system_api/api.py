import json

from gateway_service.apis.rating_system_api.schemas import UserRating
from gateway_service.config import RATING_SYSTEM_CONFIG
from gateway_service.validators import json_dump
from httpx import AsyncClient


class RatingSystemAPI:
    def __init__(self, host: str = RATING_SYSTEM_CONFIG.host, port: int = RATING_SYSTEM_CONFIG.port) -> None:
        self._host = host
        self._port = port

    async def get_rating(self, username: str) -> UserRating:
        headers = {'X-User-Name': username}
        async with AsyncClient() as client:
            response = await client.get(f'http://{self._host}:{self._port}/rating', headers=headers)

        return UserRating(**response.json())

    async def update_rating(self, username: str, new_stars: int) -> UserRating:
        headers = {'X-User-Name': username}
        body = json_dump(UserRating(stars=new_stars).dict())
        async with AsyncClient() as client:
            response = await client.post(f'http://{self._host}:{self._port}/rating', headers=headers, json=body)

        return UserRating(**response.json())
