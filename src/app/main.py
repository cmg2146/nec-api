from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.endpoints import sites
from app.settings import settings

app = FastAPI()

# configure CORS
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# add api endpoints
app.include_router(sites.router)
