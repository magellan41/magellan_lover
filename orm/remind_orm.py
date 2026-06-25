import datetime

from entity.Remind import Remind
from orm import sql_session
from utils.singleton import singleton


@singleton
class RemindORM:
    def __init__(self):
        pass

    def insert(self, task_id: str, task_name: str, prompt: str, trigger_time: datetime.datetime):
        session = sql_session.get_session()
        try:
            session.add(Remind(task_id=task_id, task_name=task_name, prompt=prompt, create_time=datetime.datetime.now(), trigger_time=trigger_time))
            session.commit()
        finally:
            session.close()

    def delete(self, task_id: str):
        session = sql_session.get_session()
        try:
            session.query(Remind).filter(Remind.task_id == task_id).update({"status": 0}, synchronize_session=False)
            session.commit()
        finally:
            session.close()

    def select_all(self):
        session = sql_session.get_session()
        try:
            return session.query(Remind).filter(Remind.status == 1).all()
        finally:
            session.close()

    def select_waiting(self):
        session = sql_session.get_session()
        try:
            return session.query(Remind).filter(Remind.status == 1, Remind.trigger_time <= datetime.datetime.now()).all()
        finally:
            session.close()
