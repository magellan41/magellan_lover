from sqlalchemy import Column, Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Location(Base):
    __tablename__ = 'location'
    id = Column(Integer, primary_key=True, autoincrement=True)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    address = Column(String(255), nullable=False)
    create_time = Column(DateTime, nullable=False)
    status = Column(Integer, nullable=False, default=1)


from pydantic import BaseModel, Field


class LocationModel(BaseModel):
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")

class LocationPoiQueryModel(LocationModel):
    longitude: float = Field(..., description="经度")
    latitude: float = Field(..., description="纬度")
    poi_type_list: list[str] = Field(..., description="地点类型列表,仅支持:餐饮服务,中餐厅,外国餐厅,快餐厅,休闲餐饮场所,购物服务")
