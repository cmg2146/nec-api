from pydantic import (
    BaseSettings,
    AnyHttpUrl,
    DirectoryPath,
    PostgresDsn
)

class AppSettings(BaseSettings):
    FASTAPI_ENV: str
    DATABASE_URL: PostgresDsn
    ALLOWED_ORIGINS: list[AnyHttpUrl] = []
    FILE_UPLOAD_DIR: DirectoryPath

    class Config:
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            if field_name == 'ALLOWED_ORIGINS':
                return [x.strip() for x in raw_val.split(",")]
            return cls.json_loads(raw_val)

settings = AppSettings()
