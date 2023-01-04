from pydantic import BaseSettings, Field


class DBConfig(BaseSettings):
    db_user: str = Field(default='program', allow_mutation=False, env='DB_USER')
    db_password: str = Field(default='test', allow_mutation=False, env='DB_PASS')
    db_host: str = Field(default='postgres', allow_mutation=False, env='DB_HOST')
    db_port: int = Field(default=5432, allow_mutation=False, env='DB_PORT')
    db_name: str = Field(default='libraries', allow_mutation=False, env='DB_NAME')

    class Config:
        validate_assignment = True


DB_CONFIG: DBConfig = DBConfig()
