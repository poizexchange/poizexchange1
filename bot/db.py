from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Float, Text
from datetime import datetime

engine = create_async_engine("sqlite+aiosqlite:///./poiz.db", echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

class Subscriber(Base):
    __tablename__ = "subscribers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Telegram ID
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    date_added: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ExchangeRequest(Base):
    __tablename__ = "exchange_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    direction: Mapped[str] = mapped_column(String)
    amount_in: Mapped[float] = mapped_column(Float)
    contact: Mapped[str | None] = mapped_column(String, nullable=True)
    requisites: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def add_subscriber(session: AsyncSession, tg_id: int, username: str | None, first_name: str | None):
    obj = await session.get(Subscriber, tg_id)
    if obj:
        obj.username = username
        obj.first_name = first_name
    else:
        obj = Subscriber(id=tg_id, username=username, first_name=first_name)
        session.add(obj)
    await session.commit()

async def all_subscribers(session: AsyncSession) -> list[Subscriber]:
    res = await session.execute(Subscriber.__table__.select())
    return res.fetchall()

async def remove_subscriber(session: AsyncSession, tg_id: int):
    await session.execute(Subscriber.__table__.delete().where(Subscriber.id == tg_id))
    await session.commit()
