from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import ForeignKey, String, Integer, Boolean, Column, BIGINT
from sqlalchemy import DateTime
from datetime import datetime

DATABASE_URL = "sqlite+aiosqlite:///./tasks.db"

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(BIGINT, unique=True, nullable=False)
    user_name = Column(String(25), nullable=False)
    tasks = relationship("Task", back_populates="user")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(BIGINT, ForeignKey("users.id"))
    title = Column(String(100), nullable=False)
    description = Column(String(2500), nullable=True)
    is_done = Column(Boolean, nullable=False, default=False)
    time_end = Column(DateTime, nullable=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="tasks")

