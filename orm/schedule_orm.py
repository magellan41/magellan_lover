import datetime

from entity.Schedule import DailySchedule, DetailSchedule
from orm import sql_session
from utils.singleton import singleton


@singleton
class DailyScheduleORM:
    def __init__(self):
        pass

    def insert(self, date, daily_schedule):
        session = sql_session.get_session()
        try:
            new_daily_schedule = DailySchedule(date=date, daily_schedule=daily_schedule)
            session.add(new_daily_schedule)
            session.commit()
        finally:
            session.close()

    def select_by_date(self, date):
        session = sql_session.get_session()
        try:
            return session.query(DailySchedule).filter(DailySchedule.date == date).first()
        finally:
            session.close()


@singleton
class DetailScheduleORM:
    def __init__(self):
        pass

    def insert(self, start_time, end_time, activity, detail):
        session = sql_session.get_session()
        try:
            new_detail_schedule = DetailSchedule(start_time=start_time,
                                                 end_time=end_time,
                                                 activity=activity,
                                                 detail=detail,
                                                 create_time=datetime.datetime.now())
            session.add(new_detail_schedule)
            session.commit()
        finally:
            session.close()

    def select_last(self):
        session = sql_session.get_session()
        try:
            return session.query(DetailSchedule).order_by(DetailSchedule.create_time.desc()).first()
        finally:
            session.close()

    def select_today(self):
        session = sql_session.get_session()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            return session.query(DetailSchedule).filter(DetailSchedule.create_time >= today).all()
        finally:
            session.close()

