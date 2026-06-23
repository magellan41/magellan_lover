import re

import openai


import logging

from schema import ModelResponseSchema
from utils import config_util, function_call_util

logger = logging.getLogger(__name__)

def init_models():
    """
    获取模型字典
    """
    llm_config = config_util.resolve_llm_config()
    model_dic = {}
    platforms = llm_config.get("platforms", [])
    if len(platforms) == 0:
        logger.error("缺少模型配置")
        raise Exception("缺少模型配置")

    for platform in platforms:
        models = platform.get("models", [])
        if len(models) == 0:
            logger.error("缺少模型配置")
            raise Exception("缺少模型配置")

        for model in models:
            model_id = platform["platform"] + "/" + model["name"]
            model_dic[model_id] = {
                "base_url": platform.get("base_url"),
                "api_key": platform.get("api_key"),
                # "key_type": platform.get("key_type"),
                "model_name": model["name"],
                "input_type": model.get("input_type"),
                "max_context_windows": model.get("max_context_windows", 131072),
            }
    return model_dic


class Llm:
    def __init__(self, base_url, api_key, model_name, agent_type):
        # print(base_url, api_key, model_name, agent_type)
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        self.agent_type = agent_type

    def chat(self, conversation):
        if self.agent_type == "chat":
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=conversation,
                tools=function_call_util.function_call_descriptions,
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=conversation
            )
        message =  response.choices[0].message
        logger.debug(f"LLM原始回复: {message.content}")
        assistant_msg = {
            "content": message.content,
        }
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": tc.function,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in message.tool_calls
            ]
        elif self.agent_type == "chat":
            # 处理结构化输出
            original_content = assistant_msg["content"]
            # json_match = re.search(r"\{.*\}", original_content, re.DOTALL)
            json_match = re.search(r"\{.*?\}", original_content, re.DOTALL)

            # 检查是否找到JSON格式
            if not json_match:
                logger.error(f"未在回复中找到JSON格式，原始内容: {original_content}")
                raise ValueError("模型未输出有效的JSON格式")

            clean_json_str = json_match.group(0)
            clean_json_str = clean_json_str.replace('“', '"').replace('”', '"')
            clean_json_str = clean_json_str.replace('‘', "'").replace('’', "'")
            logger.debug(f"json_match结果为: {clean_json_str}")
            try:
                parsed_obj = ModelResponseSchema.ChatModelResponseSchema.model_validate_json(clean_json_str)
                logger.debug(f"解析成功: {parsed_obj}")
                assistant_msg["content"] = clean_json_str
            except Exception as e:
                logger.error(f"解析失败: {e}")
                raise ValueError("模型未输出有效的JSON格式")

        return assistant_msg

        