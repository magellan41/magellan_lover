from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class DevicePushInfo(Base):
    __tablename__ = 'device_push_info'
    id = Column(Integer, primary_key=True, autoincrement=True)
    push_id = Column(String(255), nullable=False)
    create_time = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)
