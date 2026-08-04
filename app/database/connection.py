from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL
connect_args = {}

if "sslmode=" in DATABASE_URL or "channel_binding=" in DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    query = parse_qs(parsed.query, keep_blank_values=True)

    if "sslmode" in query:
        connect_args["ssl"] = True
        query.pop("sslmode", None)

    if "channel_binding" in query:
        query.pop("channel_binding", None)

    new_query = urlencode(query, doseq=True)
    DATABASE_URL = urlunparse(parsed._replace(query=new_query))

engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    connect_args=connect_args,
)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
