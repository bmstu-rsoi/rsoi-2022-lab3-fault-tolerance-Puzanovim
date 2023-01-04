from pydantic import BaseModel


class UserRating(BaseModel):
    stars: int


class RatingModel(BaseModel):
    username: str
    stars: int
    id: int

    class Config:
        orm_mode = True
