from typing import List
from uuid import UUID

from reservation_system.db.db_config import async_session
from reservation_system.db.models import Reservation, Status
from reservation_system.exceptions import NoFoundReservation
from reservation_system.service.schemas import RentedBooks, ReservationInput, ReservationModel, ReservationUpdate
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session
from sqlalchemy.future import select


class ReservationRepository:
    def __init__(self, session_factory: async_scoped_session) -> None:
        self._session_factory: async_scoped_session = session_factory

    async def get_reservations(self, username: str) -> List[ReservationModel]:
        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(select(Reservation).where(Reservation.username == username))

        reservations: List[Reservation] = result.scalars().all()

        return [ReservationModel.from_orm(reservation) for reservation in reservations]

    async def get_reservation(self, reservation_uid: UUID) -> ReservationModel:
        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(select(Reservation).where(Reservation.reservation_uid == reservation_uid))

        try:
            reservation: Reservation = result.scalar_one()
        except NoResultFound:
            raise NoFoundReservation

        return ReservationModel.from_orm(reservation)

    async def create_reservation(self, reservation: ReservationInput) -> ReservationModel:
        new_reservation = Reservation(**reservation.dict())

        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            session.add(new_reservation)
            await session.flush()
            await session.refresh(new_reservation)

        return ReservationModel.from_orm(new_reservation)

    async def delete_reservation(self, reservation_uid: UUID, username: str) -> None:
        query = (
            select(Reservation.id)
            .where(
                Reservation.reservation_uid == reservation_uid,
                Reservation.username == username,
            )
        )

        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(query)
            reservations_ids = result.scalars().all()

            await session.execute(
                delete(Reservation)  # type: ignore
                .where(Reservation.id.in_(reservations_ids))
                .execution_options(synchronize_session=False)
            )

    async def update_reservation(
            self, reservation_uid: UUID, username: str, reservation: ReservationUpdate
    ) -> ReservationModel:
        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(
                select(Reservation)
                .where(Reservation.reservation_uid == reservation_uid, Reservation.username == username)
                .with_for_update()
            )

            try:
                updated_reservation: Reservation = result.scalar_one()
            except NoResultFound:
                raise NoFoundReservation

            for key, value in reservation.dict(exclude_unset=True).items():
                if hasattr(updated_reservation, key):
                    setattr(updated_reservation, key, value)

            await session.flush()
            await session.refresh(updated_reservation)

        return ReservationModel.from_orm(updated_reservation)

    async def get_rented_books(self, username: str) -> RentedBooks:
        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(
                select(Reservation).where(Reservation.username == username, Reservation.status == Status.RENTED)
            )

            reservations: List[Reservation] = result.scalars().all()

        return RentedBooks(count=len(reservations))


reservation_repository: ReservationRepository = ReservationRepository(async_session)


def get_reservation_repository() -> ReservationRepository:
    return reservation_repository
