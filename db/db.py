from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

ASYNC_DATABASE_URL = "postgresql+asyncpg://postgres:mysecretpassword@postgres:5432/habit_bot_tg"


engine: AsyncEngine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session():
    async with async_session() as session:
        yield session

