from pydantic import BaseSettings, Field


class RatingConfig(BaseSettings):
    host: str = Field(env='RATING_SYSTEM_HOST', default='rating_system')
    port: int = Field(env='RATING_SYSTEM_PORT', default=8050)

    class Config:
        validate_assignment = True


class LibraryConfig(BaseSettings):
    host: str = Field(env='LIBRARY_SYSTEM_HOST', default='library_system')
    port: int = Field(env='LIBRARY_SYSTEM_PORT', default=8060)

    class Config:
        validate_assignment = True


class ReservationConfig(BaseSettings):
    host: str = Field(env='RESERVATION_SYSTEM_HOST', default='reservation_system')
    port: int = Field(env='RESERVATION_SYSTEM_PORT', default=8070)

    class Config:
        validate_assignment = True


RATING_SYSTEM_CONFIG: RatingConfig = RatingConfig()
LIBRARY_SYSTEM_CONFIG: LibraryConfig = LibraryConfig()
RESERVATION_SYSTEM_CONFIG: ReservationConfig = ReservationConfig()
