from sqlalchemy import Column, Float, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

Base = declarative_base()

# class Health(Base):
#     __tablename__ = 'health'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     start_time = Column(DateTime, nullable=False)
#     end_time = Column(DateTime, nullable=False)
#     source = Column(String, nullable=False)
#     unique_mark = Column(String, nullable=False)
#     create_time = Column(DateTime, nullable=False)
#     status = Column(Integer, nullable=False, default=1)
#
#     # 一对一
#     heart_rate = relationship("HeartRate", back_populates="health", uselist=False)
#     steps = relationship("Step", back_populates="health", uselist=False)
#     sleep = relationship("Sleep", back_populates="health", uselist=False)

class HeartRate(Base):
    __tablename__ = 'health_heart_rate'
    id = Column(Integer, primary_key=True, autoincrement=True)
    avg_bpm = Column(Float, nullable=False)
    max_bpm = Column(Float, nullable=False)
    min_bpm = Column(Float, nullable=False)
    latest_bpm = Column(Float, nullable=False)
    synced_time = Column(DateTime, nullable=False)
    sample_count = Column(Integer, nullable=False)
    # health_id = Column(Integer, ForeignKey('health.id'), nullable=False)
    create_time = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)

    # 一对一
    # health = relationship("Health", back_populates="heart_rate")


class Step(Base):
    __tablename__ = 'health_steps'
    id = Column(Integer, primary_key=True, autoincrement=True)
    steps = Column(Integer, nullable=False)
    synced_time = Column(DateTime, nullable=False)
    # health_id = Column(Integer, ForeignKey('health.id'), nullable=False)
    create_time = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)

    # health = relationship("Health", back_populates="steps")


# class Sleep(Base):
#     __tablename__ = 'health_sleep'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     total_minutes = Column(Integer, nullable=False)
#     synced_time = Column(DateTime, nullable=False)
#     health_id = Column(Integer, ForeignKey('health.id'), nullable=False)
#     create_time = Column(DateTime, nullable=False)
#     status = Column(Integer, nullable=False, default=1)
#
#     # 一对多：一个睡眠记录对应多个会话
#     sessions = relationship("SleepSession", back_populates="sleep")
    # 一对一
    # health = relationship("Health", back_populates="sleep")


class SleepSession(Base):
    __tablename__ = 'health_sleep_session'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # sleep_id = Column(Integer, ForeignKey('health_sleep.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    create_time = Column(DateTime, nullable=False)
    status = Column(Integer, nullable=False, default=1)

    # 多对一
    # sleep = relationship("Sleep", back_populates="sessions")
    # 一对多：一个会话包含多个阶段
    stages = relationship("SleepStage", back_populates="session")


class SleepStage(Base):
    __tablename__ = 'health_sleep_stage'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('health_sleep_session.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    stage = Column(String(15), nullable=False)
    create_time = Column(DateTime, nullable=False)
    status = Column(Integer, nullable=False, default=1)

    # 多对一
    session = relationship("SleepSession", back_populates="stages")




from pydantic import BaseModel, Field, ConfigDict
import datetime
class SleepStageModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    start_time: datetime.datetime = Field(..., description="阶段开始时间")
    end_time: datetime.datetime = Field(..., description="阶段结束时间")
    duration_minutes: int = Field(..., description="阶段持续时间（分钟）")
    stage: str = Field(..., description="睡眠阶段名称")

class SleepSessionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    start_time: datetime.datetime = Field(..., description="会话开始时间")
    end_time: datetime.datetime = Field(..., description="会话结束时间")
    duration_minutes: int = Field(..., description="会话持续时间（分钟）")
    stages: list[SleepStageModel] = Field(..., description="睡眠阶段详情列表")

class SleepModel(BaseModel):
    total_minutes: int = Field(..., description="总睡眠时间（分钟）")
    sessions: list[SleepSessionModel] = Field(..., description="睡眠阶段列表")

class HeartRateModel(BaseModel):
    avg_bpm: float = Field(..., description="平均心率（bpm）")
    max_bpm: float = Field(..., description="最大心率（bpm）")
    min_bpm: float = Field(..., description="最小心率（bpm）")
    latest_bpm: float = Field(..., description="最新心率（bpm）")
    latest_time: datetime.datetime = Field(..., description="最新心率时间")
    sample_count: int = Field(..., description="心率采样次数")

class HealthModel(BaseModel):
    start_time: datetime.datetime = Field(..., description="数据开始时间")
    end_time: datetime.datetime = Field(..., description="数据结束时间")
    heart_rate: HeartRateModel = Field(..., description="心率数据")
    sleep: SleepModel = Field(..., description="睡眠数据")
    source: str = Field(..., description="数据来源（health_connect）")
    steps: int = Field(..., description="步数")
    steps_start_time: datetime.datetime = Field(..., description="步数开始时间")
    synced_at: datetime.datetime = Field(..., description="数据同步时间")

class StepModel(BaseModel):
    steps: int = Field(..., description="步数")
    synced_time: datetime.datetime = Field(..., description="步数同步时间")


class LastDayHealthModel(BaseModel):
    sleep_sessions: list[SleepSessionModel] = Field(..., description="睡眠会话列表")
    steps: list[StepModel] = Field(..., description="步数列表")
    heart_rates: list[HeartRateModel] = Field(..., description="心率列表")


