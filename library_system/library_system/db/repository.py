from typing import Dict, List
from uuid import UUID

from library_system.db.db_config import async_session
from library_system.db.models import Book, Library, LibraryBooks
from library_system.exceptions import NoFoundBook, NoFoundLibrary, NoFoundLibraryBook
from library_system.service.schemas import BookInfo, BookInput, BookModel, LibraryInput, LibraryModel, LibraryUpdate
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session
from sqlalchemy.future import select


class LibraryRepository:
    def __init__(self, session_factory: async_scoped_session) -> None:
        self._session_factory: async_scoped_session = session_factory

    async def get_libraries(self, city: str) -> List[LibraryModel]:
        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(select(Library).where(Library.city == city))

        libraries: List[Library] = result.scalars().all()

        return [LibraryModel.from_orm(library) for library in libraries]

    async def get_library(self, library_uid: UUID) -> LibraryModel:
        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            library_query = select(Library).where(Library.library_uid == library_uid)
            result = await session.execute(library_query)

            try:
                library: Library = result.scalar_one()
            except NoResultFound:
                raise NoFoundLibrary

        return LibraryModel.from_orm(library)

    async def create_library(self, library: LibraryInput) -> LibraryModel:
        if library.library_uid is not None:
            try:
                existed_library: LibraryModel = await self.get_library(library.library_uid)
                return existed_library
            except NoFoundLibrary:
                pass

        new_library = Library(**library.dict())

        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            session.add(new_library)
            await session.flush()
            await session.refresh(new_library)

        return LibraryModel.from_orm(new_library)

    async def update_library(self, library_uid: UUID, library: LibraryUpdate) -> LibraryModel:
        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(select(Library).where(Library.library_uid == library_uid).with_for_update())

            try:
                updated_library: Library = result.scalar_one()
            except NoResultFound:
                raise NoFoundLibrary

            for key, value in library.dict(exclude_unset=True).items():
                if hasattr(updated_library, key):
                    setattr(updated_library, key, value)

            await session.flush()
            await session.refresh(updated_library)

        return LibraryModel.from_orm(updated_library)

    async def get_books(self, library_uid: UUID, show_all: bool = False) -> List[BookInfo]:
        library: LibraryModel = await self.get_library(library_uid)

        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            library_books_query = select(LibraryBooks).where(LibraryBooks.library_id == library.id)
            if not show_all:
                library_books_query.where(LibraryBooks.available_count > 0)

            result = await session.execute(library_books_query)
            library_books: List[LibraryBooks] = result.scalars().all()
            books_count: Dict[int, int] = {
                library_book.book_id: library_book.available_count for library_book in library_books
            }

            books_query = select(Book).where(Book.id.in_(books_count.keys()))
            result = await session.execute(books_query)

        books: List[Book] = result.scalars().all()

        return [BookInfo(**BookModel.from_orm(book).dict(), availableCount=books_count[book.id]) for book in books]

    async def get_book(self, book_uid: UUID) -> BookModel:
        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            book_query = select(Book).where(Book.book_uid == book_uid)
            result = await session.execute(book_query)

            try:
                book: Book = result.scalar_one()
            except NoResultFound:
                raise NoFoundBook

        return BookModel.from_orm(book)

    async def create_book(self, library_uid: UUID, book: BookInput) -> BookModel:
        library: LibraryModel = await self.get_library(library_uid)

        if book.book_uid is not None:
            try:
                existed_book: BookModel = await self.get_book(book.book_uid)
                library_book: LibraryBooks = await self.get_library_book(library.id, existed_book.id)
                return existed_book
            except (NoFoundBook, NoFoundLibraryBook):
                pass

        new_book = Book(**book.dict())

        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            session.add(new_book)
            await session.flush()
            await session.refresh(new_book)

            result = await session.execute(
                select(LibraryBooks)
                .where(LibraryBooks.library_id == library.id, LibraryBooks.book_id == new_book.id)
                .with_for_update()
            )
            try:
                library_book: LibraryBooks = result.scalar_one()
                library_book.available_count += 1
            except NoResultFound:
                library_book = LibraryBooks(book_id=new_book.id, library_id=library.id, available_count=1)
                session.add(library_book)

            await session.flush()
            await session.refresh(library_book)

        return BookModel.from_orm(new_book)

    async def update_book(self, book_uid: UUID, book: BookInput) -> BookModel:
        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(select(Book).where(Book.book_uid == book_uid).with_for_update())

            try:
                updated_book: Book = result.scalar_one()
            except NoResultFound:
                raise NoFoundLibrary

            for key, value in book.dict(exclude_unset=True).items():
                if hasattr(updated_book, key):
                    setattr(updated_book, key, value)

            await session.flush()
            await session.refresh(updated_book)

        return BookModel.from_orm(updated_book)

    async def get_library_book(self, library_id: int, book_id: int) -> LibraryBooks:
        library_book_query = select(LibraryBooks).where(
            LibraryBooks.library_id == library_id, LibraryBooks.book_id == book_id
        )

        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(library_book_query)

            try:
                library_book: Book = result.scalar_one()
            except NoResultFound:
                raise NoFoundLibraryBook

        return LibraryBooks.from_orm(library_book)

    async def update_library_book(self, library_id: int, book_id: int, change_count: int) -> None:
        library_book_query = (
            select(LibraryBooks)
            .where(LibraryBooks.library_id == library_id, LibraryBooks.book_id == book_id)
            .with_for_update()
        )

        session: AsyncSession = self._session_factory()
        async with session, session.begin():
            result = await session.execute(library_book_query)

            try:
                updated_library_book: LibraryBooks = result.scalar_one()
            except NoResultFound:
                raise NoFoundLibraryBook

            if change_count < 0 and updated_library_book.available_count < 1:
                raise PermissionError

            updated_library_book.available_count += change_count

            await session.flush()
            await session.refresh(updated_library_book)


library_repository: LibraryRepository = LibraryRepository(async_session)


def get_library_repository() -> LibraryRepository:
    return library_repository
