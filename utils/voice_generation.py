import datetime
import os
import uuid

import requests

from utils import env_util, setting

import logging
logger = logging.getLogger(__name__)



_voice_enable = "未找到该配置项"
_voice_api_key = "未找到该配置项"
_voice_generation_type = "未找到该配置项"
_voice_key_type = "未找到该配置项"


def init_voice_generation():
    """
    初始化语音合成
    """
    global _voice_enable, _voice_api_key, _voice_generation_type, _voice_key_type
    env_vars = env_util.read_env_vars(["voice_enable", "voice_key_type", "voice_api_key", "voice_generation_type"])
    _voice_generation_type = env_vars["voice_generation_type"]
    _voice_enable = env_vars["voice_enable"]
    _voice_key_type = env_vars["voice_key_type"]
    _voice_api_key = env_vars["voice_api_key"]
    if _voice_key_type == "env":
        _voice_api_key = os.getenv(_voice_api_key)



def voice_generation_minimax(api_key:str, text: str, speed: float=1.0, emotion: str="happy") -> tuple:
    """
    语音合成
    :param text: 要转换的文本
    :param speed: 语速
    :param emotion: 情感
    :return: (是否成果, 语音文件路径)
    """
    url = "https://api.minimaxi.com/v1/t2a_v2"
    payload = {
        "model": "speech-2.8-turbo",
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": "moss_audio_3dee3d0c-7ce6-11f0-8ff8-2a857e2646d2",
            "speed": speed,
            "vol": 1,
            "pitch": 1,
            "emotion": emotion
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1
        },
        "pronunciation_dict": {"tone": ["处理/(chu3)(li3)", "危险/dangerous"]},
        "subtitle_enable": False
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        response_data = response.json()
        if response_data.get("base_resp", {}).get("status_code") != 0:
            raise Exception(f"API 错误: {response_data['base_resp']['status_msg']}")

        hex_audio_str = response_data["data"]["audio"]
        audio_format = response_data["extra_info"]["audio_format"]
        audio_bytes = bytes.fromhex(hex_audio_str)

        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        output_dir = os.path.join(setting.VOICE_PATH, date_str)
        os.makedirs(output_dir, exist_ok=True)

        output_filename = f"{output_dir}/{uuid.uuid4()}.{audio_format}"
        while os.path.exists(output_filename):
            output_filename = f"{output_dir}/{uuid.uuid4()}.{audio_format}"

        with open(output_filename, "wb") as f:
            f.write(audio_bytes)
        return True, f"/static/voice/{date_str}/{output_filename.split('/')[-1]}"
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求错误: {e}")
        return False, None
    except Exception as e:
        logger.error(f"处理失败: {e}")
        return False, None


voice_generation_dic = {
    "minimax": voice_generation_minimax
}


def voice_generation(text: str) -> tuple:
    """
    语音合成入口
    """
    logger.debug(f"语音状态: {_voice_enable}，{ _voice_enable != "true"}")
    if _voice_enable != "true":
        logger.info("语音合成已禁用")
        return False, None
    if _voice_generation_type not in voice_generation_dic:
        logger.error(f"不支持的语音合成类型: {_voice_generation_type}")
        return False, None
    return voice_generation_dic[_voice_generation_type](_voice_api_key, text)
