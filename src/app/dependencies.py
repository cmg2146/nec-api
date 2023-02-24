from typing import Generator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.settings import settings

engine = create_async_engine(settings.DATABASE_URL)
# async_sessionmaker: a factory for new AsyncSession objects.
# expire_on_commit - don't expire objects after transaction commit
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

async def get_db() -> Generator:
    try:
        db = AsyncSessionLocal()
        yield db
    finally:
        db.close()
