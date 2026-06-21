import json
import re
import time


def message_argument_before_add(messages, message_type="user"):
    message = r"\n\n".join(messages)
    return f"{{\"time_stamp\": \"{time.strftime('%Y-%m-%d %H:%M CST', time.localtime())}\", \"message_type\": \"{message_type}\", \"content\": \"{message}\"}}"


def safe_json_loads(text: str):
    """安全解析 JSON，兼容 LLM 返回的包含未转义控制字符的 JSON"""
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