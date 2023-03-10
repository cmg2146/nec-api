from typing import AsyncIterator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.settings import settings

echo = settings.FASTAPI_ENV == "development"
engine = create_async_engine(settings.DATABASE_URL, echo=echo)
# async_sessionmaker: a factory for new AsyncSession objects.
# expire_on_commit - don't expire objects after transaction commit
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

async def get_db() -> AsyncIterator[AsyncSession]:
    try:
        db = AsyncSessionLocal()
        yield db
    finally:
        await db.close()
