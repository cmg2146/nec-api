from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import AnyHttpUrl, BaseSettings, validator

from app.endpoints import sites

app = FastAPI()

class AppSettings(BaseSettings):
    FASTAPI_ENV: str
    DATABASE_URL: str
    ALLOWED_ORIGINS: list[AnyHttpUrl] = []

    @validator("ALLOWED_ORIGINS", pre=True)
    def extract_allowed_origins(cls, v: str | list) -> list:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)


appSettings = AppSettings()

# configure CORS
if appSettings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in appSettings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# add api endpoints
app.include_router(sites.router)
