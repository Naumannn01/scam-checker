from pydantic_settings import BaseSettings
from sqlalchemy.dialects import postgresql

class Settings(BaseSettings):
    database_url: str
    redis_url: str

    class Config:
        env_file = ".env"


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    admin_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()