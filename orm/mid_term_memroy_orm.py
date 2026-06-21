import datetime

from entity.Memory import MidTermMemory
from orm import sql_session
from utils.singleton import singleton


@singleton
class MidTermMemoryOrm:
    def __init__(self):
        pass

    def insert(self, content):
        """
        新增中长期记忆数据
        """
        session = sql_session.get_session()
        try:
            new_mid_term_memory = MidTermMemory(content=content, create_time=datetime.datetime.now())
            session.add(new_mid_term_memory)
            session.commit()
        finally:
            session.close()

    def select_all(self):
        """
        获取所有未压缩的中长期记忆数据
        """
        session = sql_session.get_session()
        try:
            return session.query(MidTermMemory).filter(MidTermMemory.status == 1).all()
        finally:
            session.close()

    def delete(self, id):
        """
        删除中长期记忆数据
        """
        session = sql_session.get_session()
        try:
            session.query(MidTermMemory).filter(MidTermMemory.id == id).update({MidTermMemory.status: 0}, synchronize_session='fetch')
            session.commit()
        finally:
            session.close()

    def delete_all(self,ids):
        """
        删除指定的中长期记忆数据
        """
        session = sql_session.get_session()
        try:
            session.query(MidTermMemory).filter(MidTermMemory.id.in_(ids)).update({MidTermMemory.status: 0}, synchronize_session='fetch')
            session.commit()
        finally:
            session.close()

    def alive(self):
        """
        指定的中长期记忆数据增加alive_turn
        """
        session = sql_session.get_session()
        try:
            session.query(MidTermMemory).filter(
                MidTermMemory.status == 1
            ).update(
                {MidTermMemory.alive_turn: MidTermMemory.alive_turn + 1},
                synchronize_session='fetch'
            )
            session.commit()
        finally:
            session.close()

    def alive_to_long_term(self):
        """
        查询所有alive_turn大于等于15的中长期记忆数据
        """
        session = sql_session.get_session()
        try:
            return session.query(MidTermMemory).filter(MidTermMemory.alive_turn >= 15,
                                                       MidTermMemory.status == 1).all()
        finally:
            session.close()

