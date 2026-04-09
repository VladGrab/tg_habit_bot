import asyncio
from typing import List

from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP, JSONB

from .db import engine  #
from sqlalchemy import Column, Integer, String, ForeignKey, func, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=True)
    id_telegram = Column(Integer, nullable=False)
    password_hash = Column(String(255), nullable=True) # при первом запуске с чистой установить nullable=False

    def get_id(self):
        return self.id


class Habit(Base):
    __tablename__ = "habits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    time = Column(String, nullable=False)
    passed = Column(Boolean, default=0, autoincrement=True)
    count_passed = Column(Integer, default=0, autoincrement=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(),
                        autoincrement=True)

    def get_id(self):
        return self.id


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# asyncio.run(create_tables())
