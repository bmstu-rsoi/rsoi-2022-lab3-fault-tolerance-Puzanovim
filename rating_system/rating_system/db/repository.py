from rating_system.db.db_config import async_session
from rating_system.db.models import Rating
from rating_system.exceptions import NoFoundRating
from rating_system.service.schemas import RatingModel
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session
from sqlalchemy.future import select


class RatingRepository:
    def __init__(self, session_factory: async_scoped_session) -> None:
        self._session_factory: async_scoped_session = session_factory

    async def get_rating(self, username: str) -> RatingModel:
        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(select(Rating).where(Rating.username == username))

        try:
            rating: Rating = result.scalar_one()
        except NoResultFound:
            raise NoFoundRating

        return RatingModel.from_orm(rating)

    async def create_rating(self, username: str) -> RatingModel:
        new_rating = Rating(username=username, stars=1)

        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            session.add(new_rating)
            await session.flush()
            await session.refresh(new_rating)

        return RatingModel.from_orm(new_rating)

    async def update_rating(self, username: str, stars: int) -> RatingModel:
        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(select(Rating).where(Rating.username == username).with_for_update())

            try:
                updated_rating: Rating = result.scalar_one()
            except NoResultFound:
                raise NoFoundRating

            updated_rating.stars += stars
            if updated_rating.stars > 100:
                updated_rating.stars = 100
            if updated_rating.stars < 1:
                updated_rating.stars = 1

            await session.flush()
            await session.refresh(updated_rating)

        return RatingModel.from_orm(updated_rating)


rating_repository: RatingRepository = RatingRepository(async_session)


def get_rating_repository() -> RatingRepository:
    return rating_repository
