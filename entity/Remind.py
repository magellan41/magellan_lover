import datetime
from typing import List

from pydantic import BaseModel, Field
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

class RemindItem(BaseModel):
    id: int = Field(..., description="任务ID")
    prompt: str = Field(..., description="提醒提示")
    create_time: datetime.datetime = Field(..., description="创建时间")
    trigger_time: datetime.datetime = Field(..., description="触发时间")
    status: int = Field(1, description="状态：1-待触发，2-已触发，3-已取消")
    task_id: str = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")

class RemindListResponse(BaseModel):
    data: List[RemindItem] = Field(..., description="提醒列表")


