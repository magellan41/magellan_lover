import datetime

from entity.Memory import ShortTermMemory
from orm import sql_session

import logging
logger = logging.getLogger(__name__)
from utils.singleton import singleton

@singleton
class ShortTermMemoryORM:

    def __init__(self):
        pass

    def insert(self, role, content, tokens=0):
        """
        新增短期记忆数据
        """
        session = sql_session.get_session()
        try:
            new_memory = ShortTermMemory(role=role, send_time=datetime.datetime.now(), content=content, tokens=tokens)
            session.add(new_memory)
            session.commit()
        finally:
            session.close()

    def delete(self, id):
        """
        删除短期记忆数据
        """
        session = sql_session.get_session()
        try:
            session.query(ShortTermMemory.id == id).update({ShortTermMemory.status: 0}, synchronize_session='fetch')
            session.commit()
        finally:
            session.close()

    def compact(self, datetime_param, num_not_compact):
        """
        标记压缩短期记忆数据
        """
        session = sql_session.get_session()
        try:
            exclude_ids = session.query(ShortTermMemory.id).filter(
                ShortTermMemory.status == 1,
                ShortTermMemory.compact == 0,
                ShortTermMemory.send_time < datetime_param
            ).order_by(ShortTermMemory.send_time.desc()).limit(num_not_compact).all()

            exclude_id_list = [item[0] for item in exclude_ids]

            query = session.query(ShortTermMemory).filter(
                ShortTermMemory.status == 1,
                ShortTermMemory.compact == 0,
                ShortTermMemory.send_time < datetime_param)

            if exclude_id_list:
                query = query.filter(ShortTermMemory.id.notin_(exclude_id_list))

            query.update({ShortTermMemory.compact: 1}, synchronize_session='fetch')
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"压缩短期记忆数据失败，错误信息：{e}")
        finally:
            session.close()

    def get_original_memory(self):
        """
        获取所有未压缩的短期记忆数据
        """
        # return self.session.query(ShortTermMemory).filter(
        #     ShortTermMemory.status == 1,
        #     ShortTermMemory.compact == 0).all()
        session = sql_session.get_session()
        try:
            return session.query(ShortTermMemory).filter(
                ShortTermMemory.status == 1,
                ShortTermMemory.compact == 0).all()
        finally:
            session.close()

    def get_recently_memroy(self):
        """
        获取最近的100条聊天记录
        """
        session = sql_session.get_session()
        try:
            return session.query(ShortTermMemory).filter(
                ShortTermMemory.status == 1).order_by(ShortTermMemory.send_time.desc()).limit(100).all()
        finally:
            session.close()





    
    
