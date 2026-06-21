import datetime

from entity.Memory import LongTermMemory
from orm import sql_session
from utils.singleton import singleton


@singleton
class LongTermMemoryOrm:
    def __init__(self):
        pass

    def insert(self, content):
        """
        新增长期记忆数据
        """
        session = sql_session.get_session()
        try:
            new_long_term_memory = LongTermMemory(content=content, create_time=datetime.datetime.now())
            session.add(new_long_term_memory)
            session.commit()
        finally:
            session.close()

    def select_all(self):
        session = sql_session.get_session()
        try:
            long_term_memory = session.query(LongTermMemory).filter(LongTermMemory.status == 1).all()
            return long_term_memory
        finally:
                session.close()


    def delete(self, id):
        """
        删除长期记忆数据
        """
        session = sql_session.get_session()
        try:
            session.query(LongTermMemory).filter(LongTermMemory.id == id).update({LongTermMemory.status: 0}, synchronize_session=False)
            session.commit()
        finally:
            session.close()

    def delete_all(self, id_list):
        """
        批量删除长期记忆数据
        """
        session = sql_session.get_session()
        try:
            session.query(LongTermMemory).filter(LongTermMemory.id.in_(id_list)).update({LongTermMemory.status: 0}, synchronize_session=False)
            session.commit()
        finally:
            session.close()
