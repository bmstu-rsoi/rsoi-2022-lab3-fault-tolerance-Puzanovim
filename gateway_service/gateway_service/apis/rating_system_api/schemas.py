from pydantic import BaseModel


class UserRating(BaseModel):
    stars: int
