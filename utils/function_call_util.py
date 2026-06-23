import datetime
import os

import requests

from utils import env_util, common_util, setting

import logging
logger = logging.getLogger(__name__)


def download_image(image_url):
    selfie_path = os.path.join(setting.DOWNLOAD_PATH, "selfie")
    os.makedirs(selfie_path, exist_ok=True)
    image_name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    download_image_path = os.path.join(selfie_path, image_name)
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        with open(download_image_path, 'wb') as f:  # 以二进制写模式打开文件
            logger.info(f"下载图片成功，路径: {download_image_path}")
            f.write(response.content)  # 写入图片内容
    else:
        logger.error(f"下载图片失败，状态码: {response.status_code}，响应内容: {response.text}")
        raise ValueError(f"下载图片失败，状态码: {response.status_code}，响应内容: {response.text}")

    return f"/static/downloads/selfie/{image_name}"


def _generate_selfie_ark(prompt, original_image_base64, image_generator_api_key, image_generator_model):
    """
    火山平台生成图片文件
    """
    url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    headers = {
        "Authorization": f"Bearer {image_generator_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": image_generator_model,
        "prompt": prompt,
        "image": original_image_base64
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        logger.error(f"火山平台生成图片失败，状态码: {response.status_code}，响应内容: {response.text}")
        raise ValueError(f"火山平台生成图片失败，状态码: {response.status_code}，响应内容: {response.text}")
    return response.json()["data"][0]["url"]


_generate_image_dic = {
    "ark": _generate_selfie_ark
}


def _generate_selfie(prompt, original_image_base64):
    image_generator_setting = env_util.read_env_vars(["image_generator_platform", "image_generator_api_key", "image_generator_model"])
    image_generator_platform = image_generator_setting.get("image_generator_platform")
    if not image_generator_platform or image_generator_platform == "未找到该配置项":
        logger.error("未配置图片生成器平台，请前往更多配置页面配置")
        raise ValueError("未配置图片生成器平台，请前往更多配置页面配置")

    image_generator_api_key = image_generator_setting.get("image_generator_api_key")
    if not image_generator_api_key or image_generator_api_key == "未找到该配置项":
        logger.error("未配置图片生成器 API 密钥，请前往更多配置页面配置")
        raise ValueError("未配置图片生成器 API 密钥，请前往更多配置页面配置")
    image_generator_api_key = common_util.get_true_value_in_env(image_generator_api_key)

    image_generator_model = image_generator_setting.get("image_generator_model")
    if not image_generator_model or image_generator_model == "未找到该配置项":
        logger.error("未配置图片生成器模型，请前往更多配置页面配置")
        raise ValueError("未配置图片生成器模型，请前往更多配置页面配置")
    image_url = _generate_image_dic[image_generator_platform](prompt, original_image_base64, image_generator_api_key, image_generator_model)
    return download_image(image_url)


def selfie_generate(prompt):
    """
    生成自拍
    """

    character_image_path = env_util.read_env_var("character_image_path")
    if not character_image_path:
        logger.error("未配置角色图片路径，请前往更多配置页面配置")
        raise ValueError("未配置角色图片路径")
    character_image_base64 = common_util.base64_encode(character_image_path)
    return _generate_selfie(prompt, character_image_base64)



function_dic = {
    "selfie_generate": selfie_generate,
}

function_call_descriptions = [
    {
        "type": "function",
        "function": {
            "name": "selfie_generate",
            "description": "生成角色自拍,生成成功后返回图片路径，请你在回复的content字段中插入<selfie>图片路径</selfie>格式的字符串，用于向用户展示",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string","description": "自拍提示词，请详细描述人物所处的环境、人物的动作、人物的表情、人物的服装等"}
                },
                "required": ["prompt"]
            }
        }
    }
]
def execute_function(name, args):
    logger.debug(f"执行函数: {name}，参数: {args}")
    return function_dic[name](**args)