import datetime
import os
import uuid

import requests

from utils import setting


def voice_generation_minimax(text: str, speed: float=1.0, emotion: str="happy") -> tuple:
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
        "Authorization": f"Bearer {os.getenv('MINIMAX_TOKEN_PLAN_KEY')}"
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
        print(f"网络请求错误: {e}")
        return False, None
    except Exception as e:
        print(f"处理失败: {e}")
        return False, None