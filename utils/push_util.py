import hashlib
import json

import requests

from orm.device_push_id_orm import DevicePushInfoOrm
from utils import env_util

device_push_info_orm_obj = DevicePushInfoOrm()

import logging
logger = logging.getLogger(__name__)


def _get_md5_sign(params, secret_key):
    """
    生成MD5签名
    :param params_str: 排序后的参数字符串
    :param secret_key: 应用的密钥
    :return: 32位小写MD5值
    """
    sorted_items = sorted([(k, v) for k, v in params.items() if v is not None])
    basestring = ''.join([f"{k}={v}" for k, v in sorted_items])
    basestring += secret_key
    logger.debug(f"魅族推送签名原文: {basestring}")
    return hashlib.md5(basestring.encode('utf-8')).hexdigest()



def send_push_meizu(title, content):
    meizu_app_id = env_util.read_env_var('meizu_app_id')
    if meizu_app_id == "未找到该配置项":
        logger.error("未找到魅族应用ID配置项，不发送推送消息")
        return
    meizu_secret_key = env_util.read_env_var('meizu_secret_key')
    if meizu_secret_key == "未找到该配置项":
        logger.error("未找到魅族应用密钥配置项，不发送推送消息")
        return
    meizu_push_url = f"https://server-api-push.meizu.com/garcia/api/server/push/varnished/pushByPushId"
    push_id_list = device_push_info_orm_obj.select_device_push_id()
    logger.debug(f"查询到的设备推送ID: {push_id_list}")

    if not push_id_list:
        logger.debug("没有设备推送ID，不发送推送消息")
        return

    # 构建请求参数
    message_json_obj = {
        "noticeBarInfo": {
            "noticeMsgType": 1, # 私信
            "title": title,
            "content": content
        },
        "clickTypeInfo": {
            "clickType": 0  # 默认打开应用
        },
        "pushTimeInfo": {
            "offLine": 1,
            "validTime": 24
        }
    }
    message_json_str = json.dumps(message_json_obj, separators=(',', ':'), ensure_ascii=False)
    params = {
        'appId': meizu_app_id,
        'pushIds': ','.join(push_id_list),  # 转换为逗号分隔的字符串
        'messageJson': message_json_str
    }
    params['sign'] = _get_md5_sign(params, meizu_secret_key)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }

    response = requests.post(meizu_push_url, headers=headers, data=params, timeout=10)
    if response.status_code != 200:
        raise RuntimeError(f"发送推送消息失败，状态码：{response.status_code}，响应内容：{response.text}")

    response_json = response.json()
    logger.debug(f"发送推送消息响应: {response_json}")
    if response_json['code'] == 201:
        raise RuntimeError(f"发送推送消息失败,没有权限，服务器主动拒绝，状态码：{response_json['code']}，响应内容：{response_json['msg']}")
    if response_json['code'] == 501:
        raise RuntimeError(f"发送推送消息失败,推送消息失败（db_error），状态码：{response_json['code']}，响应内容：{response_json['msg']}")
    if response_json['code'] == 513:
        raise RuntimeError(f"发送推送消息失败,推送消息失败，状态码：{response_json['code']}，响应内容：{response_json['msg']}")
    if response_json['code'] == 519:
        raise RuntimeError(f"发送推送消息失败,推送消息失败服务过载，状态码：{response_json['code']}，响应内容：{response_json['msg']}")
    # 折叠不属于失败
    # if response_json['code'] == 520:
    #     raise RuntimeError(f"发送推送消息失败,消息折叠（1分钟内同一设备同一应用消息收到多次，默认5次），状态码：{response_json['code']}，响应内容：{response_json['msg']}")
    if response_json['code'] == 110002:
        raise RuntimeError(f"发送推送消息失败,pushId失效(pushId未订阅)，状态码：{response_json['code']}，响应内容：{response_json['msg']}")
    if response_json['code'] == 110003:
        raise RuntimeError(f"发送推送消息失败,pushId非法，状态码：{response_json['code']}，响应内容：{response_json['msg']}")
    if response_json['code'] == 110005:
        raise RuntimeError(f"发送推送消息失败,alias失效(alias未订阅或者消息开关关闭)，状态码：{response_json['code']}，响应内容：{response_json['msg']}")
    if response_json['code'] == 110010:
        raise RuntimeError(f"发送推送消息失败,pushId失效(消息开关关闭)，状态码：{response_json['code']}，响应内容：{response_json['msg']}")
    if response_json['code'] == 110011:
        raise RuntimeError(f"发送推送消息失败,单日公信消息数超过限制，状态码：{response_json['code']}，响应内容：{response_json['msg']}")









