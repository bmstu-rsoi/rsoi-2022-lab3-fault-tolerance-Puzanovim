import enum
import uuid

from reservation_system.db.db_config import Base
from sqlalchemy import Column, Enum, Integer, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID


class Status(enum.Enum):
    RENTED = 'RENTED'
    RETURNED = 'RETURNED'
    EXPIRED = 'EXPIRED'


class Reservation(Base):
    __tablename__ = 'reservation'

    id = Column(Integer, autoincrement=True, primary_key=True)
    reservation_uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(80), nullable=False)
    book_uid = Column(UUID(as_uuid=True), nullable=False)
    library_uid = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Enum(Status), nullable=False)
    start_date = Column(TIMESTAMP, nullable=False)
    till_date = Column(TIMESTAMP, nullable=False)
