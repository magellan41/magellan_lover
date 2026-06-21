from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime



Base = declarative_base()
class Task(Base):
    __tablename__ = 'scheduler'
    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger_type = Column(String(20), nullable=False)
    corn = Column(String(20), nullable=False)
    trigger_time = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Integer, default=1)
    is_ephemeral = Column(Boolean, default=False)
