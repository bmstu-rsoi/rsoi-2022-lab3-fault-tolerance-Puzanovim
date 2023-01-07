import logging
from typing import Any, Dict
from uuid import UUID

import uvicorn
from alembic import command
from alembic.config import Config
from fastapi import FastAPI, status
from library_system.config import DB_CONFIG
from library_system.db.db_config import SQLALCHEMY_DATABASE_URL
from library_system.db.repository import LibraryRepository, get_library_repository
from library_system.service.routers import router
from library_system.service.schemas import BookInput, Condition, LibraryInput

logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(router)


@app.get('/manage/health', status_code=status.HTTP_200_OK)
async def check_health():
    return None


@app.on_event('startup')
async def startup() -> None:
    repository: LibraryRepository = get_library_repository()
    library_uid = UUID('83575e12-7ce0-48ee-9931-51919ff3c9ee')
    library = LibraryInput(
        library_uid=library_uid,
        name='Библиотека имени 7 Непьющих',
        city='Москва',
        address='2-я Бауманская ул., д.5, стр.1',
    )
    book = BookInput(
        book_uid='f7cdc58f-2caf-4b15-9727-f89dcc629b27',
        name='Краткий курс C++ в 7 томах',
        author='Бьерн Страуструп',
        genre='Научная фантастика',
        condition=Condition.EXCELLENT,
    )
    created_library = await repository.create_library(library)
    try:
        await repository.create_book(created_library.library_uid, book)
    except Exception:
        pass


def run_db_migrations(db_config: Dict[str, Any], migration_script_location: str):
    """
    Функция запускает миграции alembic через API
    :param db_config: Конфигурация для подключения к БД
    :param migration_script_location: Путь до директории со скриптами миграций
    :return:
    """
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", migration_script_location)
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    alembic_cfg.set_main_option("standalone", 'false')
    for option in ['db_host', 'db_user', 'db_password', 'db_name']:
        if option not in db_config:
            raise Exception(f"{option} value not set")
        alembic_cfg.set_main_option(option, db_config[option])

    logger.info('Running migrations')
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        logger.exception(exc)
        raise Exception("Error while executing migrations: {}".format(exc))
    logger.info('Migrations completed')


if __name__ == "__main__":
    run_db_migrations(DB_CONFIG.dict(), 'library_system/db/migrations/')
    uvicorn.run(app, host="0.0.0.0", port=8060)
