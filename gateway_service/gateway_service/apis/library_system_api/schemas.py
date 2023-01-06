from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel


class Condition(Enum):
    EXCELLENT = 'EXCELLENT'
    GOOD = 'GOOD'
    BAD = 'BAD'
    UNKNOWN = 'UNKNOWN'


class LibraryModel(BaseModel):
    libraryUid: UUID
    name: str = ''
    city: str = ''
    address: str = ''


class BookModel(BaseModel):
    bookUid: UUID
    name: str = ''
    author: str = ''
    genre: str = ''
    condition: Condition = Condition.UNKNOWN


class BookInfo(BookModel):
    availableCount: int


class Pagination(BaseModel):
    page: int
    pageSize: int
    totalElements: int


class LibrariesPagination(Pagination):
    items: List[LibraryModel]


class BooksPagination(Pagination):
    items: List[BookInfo]
