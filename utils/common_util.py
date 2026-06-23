import base64
import io
import json
import os
import re
import time

from PIL import Image

from orm.schedule_orm import DetailScheduleORM
detail_schedule_orm_obj = DetailScheduleORM()

def base64_encode(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    img = Image.open(image_path)

    real_format = img.format

    mime_map = {
        'JPEG': 'image/jpeg',
        'PNG': 'image/png',
        'GIF': 'image/gif',
        'WEBP': 'image/webp'
    }
    mime_type = mime_map.get(real_format, 'image/jpeg')  # 默认回退到 jpeg

    buffer = io.BytesIO()
    img.save(buffer, format=real_format)
    base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:{mime_type};base64,{base64_str}"



def message_argument_before_add(messages, message_type="user"):
    # message = r"\n\n".join(messages)
    # return f"{{\"time_stamp\": \"{time.strftime('%Y-%m-%d %H:%M CST', time.localtime())}\", \"message_type\": \"{message_type}\", \"content\": \"{message}\"}}"

    text = []
    images = []
    for message_type, message_content in messages:
        if message_type == "text":
            text.append(message_content)
        elif message_type == "image":
            images.append(base64_encode(message_content))
    text = r"\n\n".join(text)

    detail_schedule = detail_schedule_orm_obj.select_last()
    activity = "无活动信息"
    if detail_schedule:
        activity =f"【活动名称】:{detail_schedule.activity}  【活动细节】:{detail_schedule.detail}"

    text = f"{{\"time_stamp\": \"{time.strftime('%Y-%m-%d %H:%M CST', time.localtime())}\", \"message_type\": \"{message_type}\", \"content\": \"{text}\", \"activity\": \"{activity}\"}}"
    res = [
        {"type": "image_url", "image_url": {"url": image}} for image in images
    ] + [{"type": "text", "text": text}]
    return res



def safe_json_loads(text: str):
    """安全解析 JSON，兼容 LLM 返回的包含未转义控制字符的 JSON"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[8:]
    if text.endswith("```"):
        text = text[:-3]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # LLM 可能在 content 字段中返回字面换行符，需要转义
        fixed = re.sub(
            r'"(?:[^"\\]|\\.)*"',
            lambda m: m.group(0).replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'),
            text
        )
        return json.loads(fixed)


def get_true_value_in_env(var_name):
    if var_name.startswith("${") and var_name.endswith("}"):
        var_val = os.environ.get(var_name[2:-1])
        if not var_val:
            raise ValueError(f"未找到环境变量 {var_name[2:-1]}")
    else:
        var_val = var_name
    return var_val

