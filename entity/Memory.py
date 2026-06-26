import datetime

from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime

Base = declarative_base()


class ShortTermMemory(Base):
    __tablename__ = 'short_term_memory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(10), nullable=False)
    content = Column(MEDIUMTEXT, nullable=False)
    send_time = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)
    compact = Column(Integer, default=0)
    tokens = Column(Integer, default=0)

class MidTermMemory(Base):
    __tablename__ = 'mid_term_memory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    create_time = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)
    alive_turn = Column(Integer, default=0)


class MidTermMemoryDto(BaseModel):
    id: int = Field(..., description="记忆ID")
    content: str = Field(..., description="记忆内容")
    create_time: datetime.datetime = Field(..., description="创建时间")
    status: int = Field(..., description="状态")
    alive_turn: int = Field(..., description="存活轮数")

class LongTermMemory(Base):
    __tablename__ = 'long_term_memory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    create_time = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)

class LongTermMemoryDto(BaseModel):
    id: int = Field(..., description="记忆ID")
    content: str = Field(..., description="记忆内容")
    create_time: datetime.datetime = Field(..., description="创建时间")
    status: int = Field(..., description="状态")
