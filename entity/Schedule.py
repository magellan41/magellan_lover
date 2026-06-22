from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class DailySchedule(Base):
    __tablename__ = 'daily_schedule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False)
    daily_schedule = Column(Text, nullable=False)


class DetailSchedule(Base):
    __tablename__ = 'detail_schedule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    activity = Column(String(20), nullable=False)
    detail = Column(Text, nullable=False)
    create_time = Column(DateTime, nullable=False)



