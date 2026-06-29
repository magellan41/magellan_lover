import datetime

from sqlalchemy.orm import joinedload

from entity.health import Step, HealthModel, HeartRate, SleepSession, SleepStage
from orm import sql_session
from utils.singleton import singleton


@singleton
class SleepSessionORM:
    def __init__(self):
        pass

    def insert(self, health_data: HealthModel):
        session = sql_session.get_session()
        try:
            current_time = datetime.datetime.now()
            # 睡眠会话数据
            for session_data in health_data.sleep.sessions:
                # 检查是否存在相同结束时间的会话
                # existence = self.select_unique_mark(session_data.end_time)
                time_tolerance = datetime.timedelta(seconds=1)
                existence = session.query(SleepSession).filter(
                    SleepSession.end_time.between(session_data.end_time - time_tolerance, session_data.end_time + time_tolerance)).first()
                if existence is not None:
                    continue
                session_orm = SleepSession(
                    start_time=session_data.start_time,
                    end_time=session_data.end_time,
                    duration_minutes=session_data.duration_minutes,
                    create_time=current_time
                )
                # 睡眠阶段数据
                for stage_data in session_data.stages:
                    stage_orm = SleepStage(
                        start_time=stage_data.start_time,
                        end_time=stage_data.end_time,
                        duration_minutes=stage_data.duration_minutes,
                        stage=stage_data.stage,
                        create_time=current_time
                    )
                    session_orm.stages.append(stage_orm)
                    # 挂载睡眠阶段数据
                # 挂载睡眠会话数据
                session.add(session_orm)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def select_unique_mark(self, synced_time):
        session = sql_session.get_session()
        try:
            time_tolerance = datetime.timedelta(seconds=1)
            existence = session.query(SleepSession).filter(SleepSession.end_time.between(synced_time - time_tolerance, synced_time + time_tolerance)).first()
            return existence
        finally:
            session.close()

    def select_last_day(self):
        current_time = datetime.datetime.now()
        last_day = current_time - datetime.timedelta(days=1)
        session = sql_session.get_session()
        try:
            sleep_sessions = session.query(SleepSession).options(joinedload(SleepSession.stages)).filter(SleepSession.end_time >= last_day).all()
            return sleep_sessions
        finally:
            session.close()

@singleton
class StepORM:
    def __init__(self):
        pass

    def insert(self, health_data: HealthModel):
        session = sql_session.get_session()
        try:
            today = datetime.datetime.today()
            existence = session.query(Step).filter(Step.synced_time >= today, Step.steps == health_data.steps).first()
            if existence is not None:
                return
            current_time = datetime.datetime.now()
            step_orm = Step(
                steps=health_data.steps,
                synced_time=health_data.synced_at,
                create_time=current_time
            )
            session.add(step_orm)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def select_unique_mark(self, steps: int):
        today =datetime.datetime.today()
        session = sql_session.get_session()
        try:
            existence = session.query(Step).filter(Step.synced_time >= today, Step.steps == steps).first()
            return existence
        finally:
            session.close()


    def select_last_day(self):
        current_time = datetime.datetime.now()
        last_day = current_time - datetime.timedelta(days=1)
        session = sql_session.get_session()
        try:
            steps = session.query(Step).filter(Step.synced_time >= last_day).all()
            return steps
        finally:
            session.close()

@singleton
class HeartRateORM:
    def __init__(self):
        pass

    def insert(self, health_data: HealthModel):
        session = sql_session.get_session()
        try:
            # existence = self.select_heart_rate(health_data.heart_rate.latest_time)
            time_tolerance = datetime.timedelta(seconds=1)
            existence = session.query(HeartRate).filter(HeartRate.synced_time.between(health_data.heart_rate.latest_time - time_tolerance, health_data.heart_rate.latest_time + time_tolerance)).first()
            if existence is not None:
                return
            current_time = datetime.datetime.now()
            heart_rate = HeartRate(
                avg_bpm=health_data.heart_rate.avg_bpm,
                max_bpm=health_data.heart_rate.max_bpm,
                min_bpm=health_data.heart_rate.min_bpm,
                latest_bpm=health_data.heart_rate.latest_bpm,
                sample_count = health_data.heart_rate.sample_count,
                synced_time=health_data.heart_rate.latest_time,
                create_time=current_time
            )
            session.add(heart_rate)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


    def select_heart_rate(self, synced_time):
        session = sql_session.get_session()
        try:
            time_tolerance = datetime.timedelta(seconds=1)
            existence = session.query(HeartRate).filter(HeartRate.synced_time.between(synced_time - time_tolerance, synced_time + time_tolerance)).first()
            return existence
        finally:
            session.close()

    def select_last_day(self):
        current_time = datetime.datetime.now()
        last_day = current_time - datetime.timedelta(days=1)
        session = sql_session.get_session()
        try:
            heart_rates = session.query(HeartRate).filter(HeartRate.synced_time >= last_day).all()
            return heart_rates
        finally:
            session.close()
