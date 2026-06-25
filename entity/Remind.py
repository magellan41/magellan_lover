from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime

Base = declarative_base()

class Remind(Base):
    __tablename__ = 'remind'
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(Text, nullable=False)
    create_time = Column(DateTime, nullable=False)
    trigger_time = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)
    task_id = Column(Text, nullable=False)
    task_name = Column(Text, nullable=False)
