import asyncio
from sqlalchemy import BigInteger, Boolean, Column, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import DB_PATH

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    uon_id = Column(String, nullable=True, index=True)
    auto_add_enabled = Column(Boolean, default=True)

engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    async with engine.begin() as conn:
        # Создание таблиц
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
