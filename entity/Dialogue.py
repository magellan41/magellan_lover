from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime

Base = declarative_base()
class DialogueHistory(Base):
    __tablename__ = 'dialog_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(10), nullable=False)
    create_time = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)
