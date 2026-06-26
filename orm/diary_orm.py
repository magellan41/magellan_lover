import datetime

from entity.Diary import Diary
from orm import sql_session
from utils.singleton import singleton


@singleton
class DiaryORM:
    def __init__(self):
        pass

    def insert(self, content):
        session = sql_session.get_session()
        try:
            current_date_time = datetime.datetime.now()
            diary = Diary(title=current_date_time.strftime("%Y-%m-%d"), content=content, create_time=current_date_time)
            session.add(diary)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def list_diary_titles(self, mini_id: int):
        session = sql_session.get_session()
        try:
            query = session.query(Diary.id, Diary.title).filter(Diary.status == 1)
            if mini_id != -1:
                query = query.filter(Diary.id < mini_id)
            return [{"id": id, "title": title} for (id, title) in query.order_by(Diary.id.desc()).limit(100).all()]
        finally:
            session.close()

    def select_diary_by_id(self, id: int):
        session = sql_session.get_session()
        try:
            diary = session.query(Diary).filter(Diary.id == id).first()
            return diary
        finally:
            session.close()

