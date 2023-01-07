from typing import List
from uuid import UUID

from library_system.db.models import Condition
from pydantic import BaseModel


class LibraryInput(BaseModel):
    name: str
    city: str
    address: str
    library_uid: UUID | None

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class LibraryUpdate(LibraryInput):
    name: str | None
    city: str | None
    address: str | None


class LibraryModel(LibraryInput):
    id: int
    library_uid: UUID


class LibraryResponse(LibraryInput):
    libraryUid: UUID


class BookInput(BaseModel):
    name: str
    author: str
    genre: str
    condition: Condition
    book_uid: UUID | None

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class BookUpdate(BookInput):
    name: str | None
    author: str | None
    genre: str | None
    condition: Condition | None


class BookModel(BookInput):
    id: int
    book_uid: UUID


class BookInfo(BookModel):
    availableCount: int


class BookInfoResponse(BookInput):
    bookUid: UUID
    availableCount: int


class BookResponse(BookInput):
    bookUid: UUID


class ListResponse(BaseModel):
    page: int
    pageSize: int
    totalElements: int
    items: List


class LibrariesResponse(ListResponse):
    items: List[LibraryResponse]


class BooksResponse(ListResponse):
    items: List[BookInfoResponse]
