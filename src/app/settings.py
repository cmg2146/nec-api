from pydantic import AnyHttpUrl, BaseSettings, FilePath, PostgresDsn, validator

class AppSettings(BaseSettings):
    FASTAPI_ENV: str
    DATABASE_URL: PostgresDsn
    ALLOWED_ORIGINS: list[AnyHttpUrl] = []
    FILE_UPLOAD_DIR: FilePath

    @validator("ALLOWED_ORIGINS", pre=True)
    def extract_allowed_origins(cls, v: str | list) -> list:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)


settings = AppSettings()
