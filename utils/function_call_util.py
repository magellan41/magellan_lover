import datetime
import os

import requests

from utils import env_util, common_util, setting, embedding_util

import logging
logger = logging.getLogger(__name__)


def _download_image(image_url):
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
    logger.info(f"火山平台生成图片成功")
    return response.json()["data"][0]["url"]


def _generate_selfie_ali(prompt, original_image_base64, image_generator_api_key, image_generator_model):
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers = {
        "Authorization": f"Bearer {image_generator_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": image_generator_model,
        "input": {
            "messages": [{
                "role": "user",
                "content": [
                    {"image": original_image_base64},
                    {"text": prompt}
                ]
            }]
        },
        "parameters": {
            "n": 1,
            "negative_prompt": " ",
            "prompt_extend": True,
            "watermark": False,
            "size": "2048*2048"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        logger.error(f"阿里云平台生成图片失败，状态码: {response.status_code}，响应内容: {response.text}")
        raise ValueError(f"阿里云平台生成图片失败，状态码: {response.status_code}，响应内容: {response.text}")
    logger.info(f"阿里云平台生成图片成功")
    return response.json()['output']['choices'][0]['message']['content'][0]['image']


def _generate_selfie_minimax(prompt, original_image_base64, image_generator_api_key, image_generator_model):
    url = "https://api.minimaxi.com/v1/image_generation"
    headers = {
        "Authorization": f"Bearer {image_generator_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": image_generator_model,
        "prompt": prompt,
        "aspect_ratio": "1:1",
        "subject_reference": [{
            "type": "character",
            "image_file": original_image_base64
        }],
        "n": 1
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        logger.error(f"minimax平台生成图片失败，状态码: {response.status_code}，响应内容: {response.text}")
        raise ValueError(f"minimax平台生成图片失败，状态码: {response.status_code}，响应内容: {response.text}")
    logger.info(f"minimax平台生成图片成功")
    return response.json()["data"]["image_urls"][0]

def _generate_selfie_agnes(prompt, original_image_base64, image_generator_api_key, image_generator_model):
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {image_generator_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": image_generator_model,
        "size": "1024x1024",
        "prompt": prompt,
        "extra_body": {
            "image": [
                original_image_base64
            ],
            "response_format": "url"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        logger.error(f"agnes平台生成图片失败，状态码: {response.status_code}，响应内容: {response.text}")
        raise ValueError(f"agnes平台生成图片失败，状态码: {response.status_code}，响应内容: {response.text}")
    logger.info(f"agnes平台生成图片成功")
    return response.json()["data"][0]["url"]

_generate_image_dic = {
    "ark": _generate_selfie_ark,
    "ali": _generate_selfie_ali,
    "minimax": _generate_selfie_minimax,
    "agnes": _generate_selfie_agnes
}

def list_image_generator_platform():
    return _generate_image_dic.keys()


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
    return _download_image(image_url)


def selfie_generate(prompt):
    """
    生成自拍
    """

    character_image_path = env_util.read_env_var("character_image_path")
    if not character_image_path:
        logger.error("未配置角色图片路径，请前往更多配置页面配置")
        raise ValueError("未配置角色图片路径")
    character_image_base64 = common_util.base64_encode(character_image_path)
    prompt = f"请你根据所提供的图片人物为模特，根据提示生成自拍图片，{prompt}，请保证图片画风真实"
    return _generate_selfie(prompt, character_image_base64)



def query_memes_by_text(query_text: str):
    return str(embedding_util.query_memes_by_text(query_text))


function_dic = {
    "selfie_generate": selfie_generate,
    "query_memes_by_text": query_memes_by_text,
}

function_call_descriptions = [
    {
        "type": "function",
        "function": {
            "name": "selfie_generate",
            "description": "生成角色自拍,生成成功后返回图片路径。请你在回复的`content`部分中插入<selfie>图片路径</selfie>格式的字符串，用于向用户展示，不需要用户主动要求，你可以自主决定发送自拍。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string","description": "自拍提示词，请详细描述人物所处的环境、人物的动作、人物的表情、人物的服装等，人物用模特指代"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_memes_by_text",
            "description": "根据文本查询表情包,文本可以是想要表达的情感，想说的话，工具通过语义匹配返回表情包id以及对表情包的描述。你可以使用<memes>表情包id</memes>格式的字符串插入到回复的`content`部分中，用于向用户发送表情包，不需要用户主动要求，你可以自主决定发送表情包。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_text": {"type": "string","description": "用于文搜图的文本，可以是想要表达的情感，想说的话"}
                },
                "required": ["query_text"]
            }
        }
       }
]
def execute_function(name, args):
    logger.debug(f"执行函数: {name}，参数: {args}")
    return function_dic[name](**args)

if __name__ == "__main__":
    import base64
    base64_str = f"data:image/png;base64,{base64.b64encode(open(r"D:\magellan_data\code_workspace\python_workspace\magellan_lover\static\uploads\character_image\character_image.png", "rb").read()).decode('utf-8')}"
    image_u = _generate_selfie_agnes("角色在房间内，房间内有灯，灯是黄色的", base64_str, os.getenv("AGNES_API_KEY"), "agnes-image-2.1-flash")
    print(image_u)
