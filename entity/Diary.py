from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime


Base = declarative_base()

class Diary(Base):
    __tablename__ = 'diary'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    create_time = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)


class DiaryDto(BaseModel):
    title: str = Field(..., description="日记标题")
    content: str = Field(..., description="日记内容")


