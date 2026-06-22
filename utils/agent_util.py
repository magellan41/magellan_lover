import datetime
import json
import os
import logging
import threading

from orm.long_term_memory_orm import LongTermMemoryOrm
from orm.mid_term_memroy_orm import MidTermMemoryOrm
from orm.short_term_memory_orm import ShortTermMemoryORM
from utils.common_util import message_argument_before_add
from utils.llm_util import Llm
from utils import setting, env_util, llm_util, config_util

logger = logging.getLogger(__name__)

short_term_memory_orm_obj = ShortTermMemoryORM()
mid_term_memory_orm_obj = MidTermMemoryOrm()
long_term_memory_orm_obj = LongTermMemoryOrm()

def estimate_tokens(text: str) -> int:
    """
    基于启发式规则的通用 Token 估算
    """
    if not text:
        return 0

    # 基础经验值：英文约 1 Token / 4 字符，中文约 1.5 Token / 字
    # 此处采用保守估算，防止上下文压缩时超出窗口
    cn_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    other_chars = len(text) - cn_chars

    estimated_tokens = int(cn_chars * 1.5 + other_chars * 0.35)
    return max(1, estimated_tokens)


class Agent:
    def __init__(self, base_url, api_key, model_name, input_type, system_prompt, continuous_dialogue=False, max_context_windows=131072):
        self.llm = Llm(base_url, api_key, model_name)

        self.input_type = input_type
        self.system_prompt = system_prompt
        self.continuous_dialogue = continuous_dialogue
        self.max_context_windows = max_context_windows



        self.total_tokens = estimate_tokens(self.system_prompt)
        self.conversation = None
        self.init_conversation()

        self.compact_running = threading.Event()
        self.conversation_not_in_compact_indx = -1

    def init_conversation(self):
        self.conversation = [
            {"role": "system", "content": self.system_prompt}
        ]
        history_dialogues = short_term_memory_orm_obj.get_original_memory()
        for dialogue in history_dialogues:
            self.conversation.append({"role": dialogue.role, "content": dialogue.content})
            self.total_tokens += dialogue.tokens
        logger.debug(f"conversation: {self.conversation}, total_tokens: {self.total_tokens}")

    # def add_messages(self, role, messages):
    #     for message in messages:
    #         self.add_message(role, message)

    def add_message(self, role, message):
        tokens = estimate_tokens(message)
        short_term_memory_orm_obj.insert(role, message, tokens)
        self.total_tokens += tokens
        self.conversation.append({"role": role, "content": message})



    def chat(self, messages, message_type="user"):
        # logger.debug(f"chat: {self.continuous_dialogue}")
        message = message_argument_before_add(messages, message_type)
        if self.continuous_dialogue:
            self.add_message("user", message)
        else:
            self.conversation.append({"role": "user", "content": message})

        res = self.llm.chat(self.conversation)
        # logger.info(f"回复消息: {res}")
        if self.continuous_dialogue:
            self.add_message("assistant", res)

        # 记录用户最后一次回复的消息
        if message_type == "user":
            env_util.write_env_var(
                "last_interaction_time",
                datetime.datetime.now().isoformat())

        # 持久化对话需要压缩
        if self.continuous_dialogue:
            self.compact()
        else:
            self.conversation = [
                {"role": "system", "content": self.system_prompt}
            ]
            self.total_tokens = estimate_tokens(self.system_prompt)

        return res

    # TODO: 压缩未测试
    def compact_history(self):
        compact_time = datetime.datetime.now()
        compact_agent = agents["compact"]
        # 保留最近6条消息不压缩
        self.conversation_not_in_compact_indx = len(compact_agent.conversation) - 6
        # 压缩消息
        compact_content = self.conversation[1:-6].copy()
        res = compact_agent.chat(str(compact_content), message_type="system")
        # 更新系统提示
        new_system_prompt = self.system_prompt + "【历史对话记录摘要】：\n" + res
        # 计算新的 Token 数量
        history_conversation_not_compact = self.conversation[self.conversation_not_in_compact_indx:]
        self.total_tokens = estimate_tokens(new_system_prompt) + sum(estimate_tokens(message["content"]) for message in history_conversation_not_compact)
        # 新的对话记录
        self.conversation = [{"role": "system", "content": new_system_prompt}] + self.conversation[self.conversation_not_in_compact_indx:]
        # 标记压缩短期记忆数据
        short_term_memory_orm_obj.compact(compact_time)
        # 新增中期记忆
        mid_term_memory_orm_obj.insert(res)

    def compact(self):
        if self.total_tokens > self.max_context_windows * 0.5 and not self.compact_running.is_set():
            self.compact_running.set()
            try:
                thread = threading.Thread(target=self.compact_history)
                thread.start()
            finally:
                self.compact_running.clear()



agents = {}




def get_all_memory():
    mid_term_memory_list = mid_term_memory_orm_obj.select_all()
    long_term_memory_list = long_term_memory_orm_obj.select_all()

    if mid_term_memory_list:
        mid_term_memory_str = "\n".join([memory.content for memory in mid_term_memory_list])
    else:
        mid_term_memory_str = "暂无中期记忆"

    if long_term_memory_list:
        long_term_memory_str = "\n".join([memory.content for memory in long_term_memory_list])
    else:
        long_term_memory_str = "暂无长期记忆"
    return mid_term_memory_str, long_term_memory_str



def init_agents():
    model_dic = llm_util.init_models()

    llm_config = config_util.resolve_llm_config()
    agents_config = llm_config.get("agents", {})
    if len(agents_config) == 0:
        logger.error("缺少agents配置")
        raise Exception("缺少agents配置")

    max_compact_tokens = model_dic[agents_config['chat']].get("max_compact_tokens", 131072) * 0.1
    soul = ""
    with open(os.path.join(setting.CONFIG_PATH, "soul.md"),  "r", encoding="utf-8") as f:
        soul = f.read().strip()
    user = ""
    with open(os.path.join(setting.CONFIG_PATH, "user.md"),  "r", encoding="utf-8") as f:
        user = f.read().strip()
    mid_term_memory_str, long_term_memory_str = get_all_memory()
    agents_dic = {}
    for agent_type, model_id in agents_config.items():
        model_config = model_dic.get(model_id)
        if model_config is None:
            logger.error(f"缺少{agent_type}模型配置{model_id}")
            raise Exception(f"缺少{agent_type}模型配置{model_id}")

        key_type = model_config["key_type"]
        if key_type == "env":
            api_key = os.getenv(model_config["api_key"])
        else:
            api_key = model_config["api_key"]

        system_prompt_path = os.path.join(setting.CONFIG_PATH, agent_type + "_system_prompt.txt")
        system_prompt = 'You are a helpful assistant.'
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
        system_prompt = system_prompt.format(max_compact_tokens=max_compact_tokens, mid_term_memory=mid_term_memory_str, long_term_memory=long_term_memory_str, soul=soul, user=user)
        logger.debug(model_config)
        agents_dic[agent_type] = Agent(model_config["base_url"],
                                     api_key, model_config["model_name"],
                                     model_config["input_type"],
                                     system_prompt,
                                     True if agent_type == "chat" else False,
                                     model_config.get("max_context_windows"))
    global agents
    agents = agents_dic
    return agents_dic



    


