from rating_system.db.db_config import Base
from sqlalchemy import Column, Integer, String


class Rating(Base):
    __tablename__ = 'rating'

    id = Column(Integer, autoincrement=True, primary_key=True)
    username = Column(String(80), nullable=False)
    stars = Column(Integer, nullable=False)
