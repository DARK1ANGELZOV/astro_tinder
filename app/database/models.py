import os
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

from sqlalchemy import DateTime, Boolean, BigInteger, Float, Integer, String, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

load_dotenv()
# По умолчанию используем SQLite файл в корне проекта, если не задано иное в окружении
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    project_root = Path(__file__).resolve().parents[2]
    db_file = project_root / 'database.sqlite3'
    # Используем aiosqlite для асинхронного доступа
    DATABASE_URL = f"sqlite+aiosqlite:///{db_file.as_posix()}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    name: Mapped[str] = mapped_column(String(50))
    age: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(50))

    photo1: Mapped[str] = mapped_column(String(128), nullable=True)
    photo2: Mapped[str] = mapped_column(String(128), nullable=True)
    photo3: Mapped[str] = mapped_column(String(128), nullable=True)
    video: Mapped[str] = mapped_column(String(128), nullable=True)

    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)

    instagram: Mapped[str] = mapped_column(String(64), nullable=True)
    phone: Mapped[str] = mapped_column(String(16), nullable=True)

    is_search: Mapped[bool] = mapped_column(Boolean, default=False)
    min_age: Mapped[int] = mapped_column(Integer, nullable=True)
    max_age: Mapped[int] = mapped_column(Integer, nullable=True)

    gender: Mapped[str] = mapped_column(String(1))  # M/W
    seeking_gender: Mapped[str] = mapped_column(String(1))  # M/W/N

    is_registered: Mapped[bool] = mapped_column(Boolean, default=False)

    lang_code: Mapped[str] = mapped_column(String(4), nullable=True)

    index_field: Mapped[int] = mapped_column(Integer, nullable=True)

    username: Mapped[str] = mapped_column(String(255), nullable=True)


class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    to_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user1: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    user2: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
