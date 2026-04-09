from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


# ASYNC_DATABASE_URL = "postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/habit_bot_tg"
# SYNC_DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost:5432/habit_bot_tg"

ASYNC_DATABASE_URL = "postgresql+asyncpg://postgres:mysecretpassword@postgres:5432/habit_bot_tg"
SYNC_DATABASE_URL = "postgresql://postgres:mysecretpassword@postgres:5432/habit_bot_tg"

engine: AsyncEngine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Session = scoped_session(async_session)


async def get_async_session():
    async with async_session() as session:
        yield session

jobstores = {
    'tg_reminder': SQLAlchemyJobStore(url=SYNC_DATABASE_URL)
}

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Europe/Moscow")
