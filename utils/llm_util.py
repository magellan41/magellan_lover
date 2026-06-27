import httpx
import openai


import logging

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
        # 设置超时时间，防止LLM调用阻塞
        self.client = openai.OpenAI(api_key=api_key,
                                    base_url=base_url,
                                    timeout=httpx.Timeout(connect=10.0, read=300.0, write=20.0, pool=10.0))
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
        usage = response.usage
        logger.debug(f"LLM原始回复: {message.content}")
        assistant_msg = {
            "content": message.content,
        }
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in message.tool_calls
            ]

        return assistant_msg, usage.total_tokens