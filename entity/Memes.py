from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class Memes(Base):
    __tablename__ = 'memes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    md5_val = Column(String(255), nullable=False)
    try_to_save_vector = Column(Integer, default=0)
    vector_status = Column(Integer, default=0)
    status = Column(Integer, default=1)
