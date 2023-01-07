from fastapi import APIRouter, Depends, Header, status
from rating_system.db.repository import RatingRepository, get_rating_repository
from rating_system.exceptions import NoFoundRating
from rating_system.service.schemas import RatingModel, UserRating

router = APIRouter()


@router.get('/rating', status_code=status.HTTP_200_OK, response_model=UserRating)
async def get_rating(
    x_user_name: str = Header(), rating_repository: RatingRepository = Depends(get_rating_repository)
) -> UserRating:
    try:
        user_rating: RatingModel = await rating_repository.get_rating(x_user_name)
    except NoFoundRating:
        user_rating: RatingModel = await rating_repository.create_rating(x_user_name)
    return UserRating(stars=user_rating.stars)


@router.post('/rating', status_code=status.HTTP_201_CREATED, response_model=UserRating)
async def get_rating(
    new_stars: UserRating,
    x_user_name: str = Header(),
    rating_repository: RatingRepository = Depends(get_rating_repository)
) -> UserRating:
    user_rating: RatingModel = await rating_repository.update_rating(x_user_name, new_stars.stars)
    return UserRating(stars=user_rating.stars)
