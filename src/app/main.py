from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.endpoints import sites, surveys, overlays, assets, asset_types, panos, photos
from app.settings import settings

app = FastAPI(title="NEC API")

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
app.include_router(asset_types.router)
app.include_router(sites.router)
app.include_router(surveys.router)
app.include_router(overlays.router)
app.include_router(panos.router)
app.include_router(assets.router)
app.include_router(photos.router)

# add a simple healthcheck endpoint
@app.head('/healthcheck/')
def get_healthcheck():
    pass
