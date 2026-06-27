import datetime

from entity.DevicePushInfo import DevicePushInfo
from orm import sql_session
from utils.singleton import singleton

import logging

logger = logging.getLogger(__name__)


@singleton
class DevicePushInfoOrm:
    def __init__(self):
        self.device_push_info_list = None

    def insert_device_push_id(self, push_id: str):
        session = sql_session.get_session()
        try:
            exist = session.query(DevicePushInfo).filter(DevicePushInfo.push_id == push_id, DevicePushInfo.status == 1).first()
            if exist is not None:
                return
            new_device_push_info = DevicePushInfo(push_id=push_id, create_time=datetime.datetime.now())
            session.add(new_device_push_info)
            self.device_push_info_list = None
            session.commit()
        finally:
            session.close()

    def select_device_push_id(self):
        logger.debug("查询设备推送ID")
        if self.device_push_info_list is not None:
            return self.device_push_info_list
        session = sql_session.get_session()
        try:
            device_push_info = session.query(DevicePushInfo).filter(DevicePushInfo.status == 1).all()
            if device_push_info is None:
                return []
            else:
                return [item.push_id for item in device_push_info]
        except Exception as e:
            logger.error(f"查询设备推送ID失败: {e}")
            return []
        finally:
            session.close()

    def delete_device_push_id(self, push_id: str):
        session = sql_session.get_session()
        try:
            session.query(DevicePushInfo).filter(DevicePushInfo.push_id == push_id).update({"status": 0}, synchronize_session=False)
            self.device_push_info_list = None
            session.commit()
        except Exception as e:
            logger.error(f"删除设备推送ID失败: {e}")
        finally:
            session.close()
