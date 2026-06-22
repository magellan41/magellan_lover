import datetime
from typing import List, Any

from entity.Dialogue import DialogueHistory
from utils.singleton import singleton
from orm import sql_session

@singleton
class DialogueHistoryOrm:
    def __init__(self):
        pass

    def insert(self, content: str, role: str, content_type: str):
        session = sql_session.get_session()
        try:
            new_dialogue_history = DialogueHistory(role=role, content=content, type=content_type, create_time=datetime.datetime.now())
            session.add(new_dialogue_history)
            session.commit()
        finally:
            session.close()

    def list(self, min_id:int):
        session = sql_session.get_session()
        try:
            if min_id == -1:
                return session.query(DialogueHistory).order_by(DialogueHistory.create_time.desc()).limit(12).all()
            return session.query(DialogueHistory).filter(DialogueHistory.id < min_id).order_by(DialogueHistory.create_time.desc()).limit(12).all()
        finally:
            session.close()



