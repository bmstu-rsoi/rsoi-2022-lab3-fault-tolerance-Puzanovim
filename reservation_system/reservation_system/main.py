import logging
from typing import Any, Dict

import uvicorn
from alembic import command
from alembic.config import Config
from fastapi import FastAPI, status
from reservation_system.config import DB_CONFIG
from reservation_system.db.db_config import SQLALCHEMY_DATABASE_URL
from reservation_system.service.routers import router

logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(router)


@app.get('/manage/health', status_code=status.HTTP_200_OK)
async def check_health():
    return None


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
    run_db_migrations(DB_CONFIG.dict(), 'reservation_system/db/migrations/')
    uvicorn.run(app, host="0.0.0.0", port=8070)
