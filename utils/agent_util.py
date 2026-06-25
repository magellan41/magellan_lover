import datetime
import json
import os
import logging
import threading

from entity.config import RoughSchedule
from orm.long_term_memory_orm import LongTermMemoryOrm
from orm.mid_term_memroy_orm import MidTermMemoryOrm
from orm.short_term_memory_orm import ShortTermMemoryORM
from utils.common_util import message_argument_before_add
from utils.llm_util import Llm
from utils import setting, env_util, llm_util, config_util, common_util, function_call_util

logger = logging.getLogger(__name__)

short_term_memory_orm_obj = ShortTermMemoryORM()
mid_term_memory_orm_obj = MidTermMemoryOrm()
long_term_memory_orm_obj = LongTermMemoryOrm()

def estimate_tokens(messages) -> int:
    """
    基于启发式规则的通用 Token 估算
    """
    if not messages:
        return 0

    total_cn_chars = 0
    total_other_chars = 0

    if not isinstance(messages, list):
        messages = [messages]

    for msg in messages:
        content = msg.get("content", "")

        if isinstance(content, str):
            text_to_count = content

        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif item.get("type") == "image_url":
                    # 提取 Base64 数据参与字符统计
                    url = item.get("image_url", {}).get("url", "")
                    if url.startswith("data:"):
                        base64_data = url.split(",", 1)[-1]
                        text_parts.append(base64_data)
            text_to_count = "".join(text_parts)
        else:
            continue

        # 统计中英文字符数
        cn_chars = sum(1 for char in text_to_count if '\u4e00' <= char <= '\u9fff')
        other_chars = len(text_to_count) - cn_chars

        total_cn_chars += cn_chars
        total_other_chars += other_chars

        # 基础经验值：中文约 1.5 Token / 字，英文/Base64 约 1 Token / 3~4 字符
    estimated_tokens = int(total_cn_chars * 1.5 + total_other_chars * 0.35)

    # 加上消息结构本身的开销（如 role, type 等系统级 Token）
    structure_overhead = len(messages) * 5

    return max(1, estimated_tokens + structure_overhead)


class Agent:
    def __init__(self, base_url, api_key, model_name, input_type, system_prompt, agent_type, continuous_dialogue=False, max_context_windows=131072):
        self.llm = Llm(base_url, api_key, model_name, agent_type)

        self.input_type = input_type
        self.system_prompt = system_prompt
        self.continuous_dialogue = continuous_dialogue
        self.max_context_windows = max_context_windows
        self.agent_type = agent_type

        self.total_tokens = 0
        self.conversation = None
        self.init_conversation()

        self.compact_running = threading.Event()
        self.conversation_not_in_compact_indx = -1

    def could_input_image(self):
        return self.input_type is not None and "image" in self.input_type

    def init_conversation(self):
        self.conversation = [
            {"role": "system", "content": self.system_prompt}
        ]
        # self.total_tokens = estimate_tokens(self.conversation)
        if self.agent_type == "chat":
            history_dialogues = short_term_memory_orm_obj.get_original_memory()
            for dialogue in history_dialogues:
                dialogue_json = common_util.safe_json_loads(dialogue.content)
                if dialogue_json['role'] == "user" and "image" not in self.input_type:
                    content = dialogue_json['content']
                    if isinstance(content, list):
                        content = [item for item in content if item.get("type") == "text"]
                        logger.debug(f"文本模型去除图片后: {content}")
                        if len(content) == 0:
                            content = [{"type": "text", "text": "用户发送了一张图片"}]
                    dialogue_json['content'] = content
                self.conversation.append(dialogue_json)
                # self.total_tokens += dialogue.tokens
        logger.debug(f"conversation: {self.conversation}")

    # def add_messages(self, role, messages):
    #     for message in messages:
    #         self.add_message(role, message)

    def add_message(self, role, message):
        if role == "tool":
            message_in_conversation = {"role": role, "content": message["content"], "tool_call_id": message["tool_call_id"]}
        elif role == "assistant" or role is None:
            message_in_conversation = message.copy()
            message_in_conversation["role"] = "assistant"
        else:
            message_in_conversation = {"role": role, "content": message}
        # tokens = estimate_tokens(message_in_conversation)
        # self.total_tokens += tokens
        self.conversation.append(message_in_conversation)

        message_in_db = json.dumps(message_in_conversation, ensure_ascii=False)
        logger.debug(f" role: {role}, type: {type(message_in_db)} message_in_db: {message_in_db}")
        short_term_memory_orm_obj.insert(role, message_in_db, 0)



    def chat(self, messages, message_type="user"):
        """
        chat agent接收[(text, content), (image, path)...]
        memes agent接收base64编码的图片字符串
        其它agent接收content
        """
        # logger.debug(f"chat: {self.continuous_dialogue}")
        try:
            logger.debug(f"agent_type: {self.agent_type}")
            if self.agent_type == "chat":
                if isinstance(messages, str):
                    messages = [("text", messages)]
                message = message_argument_before_add(messages, message_type)
            elif self.agent_type == "memes":
                message = [
                    {"type": "image_url", "image_url": {"url": messages}},
                    {"type": "text", "text": "请你解释表情包的含义,返回表情包的具体内容、表情包的含义、表情包的使用场景。不需要添加任何问候或前缀（如“好的”、“以下是表情包的解析”等）。"}
                ]
            else:
                message = messages
            if self.continuous_dialogue:
                self.add_message("user", message)
            else:
                self.conversation.append({"role": "user", "content": message})
            logger.debug(f"当前conversation: {self.conversation}")
            max_tools_call = 20
            max_formate_retry = 5
            tools_call = 0
            formate_retry = 0
            response_message = None
            while tools_call < max_tools_call and formate_retry < max_formate_retry:
                try:
                    response_message, tokens_used = self.llm.chat(self.conversation)
                    self.total_tokens = tokens_used
                    logger.debug(f"当前total_tokens: {self.total_tokens}")
                except ValueError:
                    logger.error(f"模型输出格式错误,重试中,第{formate_retry+1}次")
                    formate_retry += 1
                    continue
                # logger.info(f"回复消息: {res}")
                if self.continuous_dialogue and response_message:
                    self.add_message("assistant", response_message)
                # tool_call处理
                if response_message.get("tool_calls"):
                    logger.debug("工具调用:")
                    for tool_call in response_message["tool_calls"]:
                        logger.debug(f"调用 ID: {tool_call['id']}")
                        logger.debug(f"函数名称: {tool_call['function']['name']}")
                        logger.debug(f"参数: {tool_call['function']['arguments']}")
                        args = common_util.safe_json_loads(tool_call['function']['arguments'])
                        try:
                            result = function_call_util.execute_function(tool_call['function']['name'], args)
                        except Exception as e:
                            logger.error(f"函数调用失败,详细信息: {e}")
                            result = f"函数调用失败,详细信息: {e}"
                        logger.debug(f"函数返回结果: {result}")
                        self.add_message("tool",{"content": result,"tool_call_id": tool_call['id']})
                        tools_call += 1
                else:
                    break

            if response_message is None:
                return f"【ERROR】: 模型输出为空,尝试工具调用次数{tools_call},模型输出格式错误重试次数{formate_retry}：{"工具调用链过长" if tools_call > max_tools_call else "模型输出格式错误重试失败"}"
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
                # self.total_tokens = estimate_tokens(self.conversation)

            return response_message["content"]
        except Exception as e:
            logger.error(f"chat失败,详细信息: {e}")
            return f"【ERROR】: {e}"


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
        # 新的对话记录
        self.conversation = [{"role": "system", "content": new_system_prompt}] + self.conversation[self.conversation_not_in_compact_indx:]
        # 重置 Token 数量
        self.total_tokens = 0
        # 标记压缩短期记忆数据
        short_term_memory_orm_obj.compact(compact_time)
        # 新增中期记忆
        mid_term_memory_orm_obj.insert(res)

    def compact(self):
        if self.total_tokens > self.max_context_windows * 0.5 and not self.compact_running.is_set():
            self.compact_running.set()
            # 双重检查，避免重复压缩
            if self.total_tokens > self.max_context_windows * 0.5:
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

        api_key = model_config["api_key"]
        api_key = common_util.get_true_value_in_env(api_key)
        # key_type = model_config["key_type"]
        # if key_type == "env":
        #     api_key = os.getenv(model_config["api_key"])
        # else:
        #     api_key = model_config["api_key"]

        system_prompt_path = os.path.join(setting.CONFIG_PATH, agent_type + "_system_prompt.txt")
        system_prompt = 'You are a helpful assistant.'
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
        system_prompt = system_prompt.format(max_compact_tokens=max_compact_tokens, mid_term_memory=mid_term_memory_str, long_term_memory=long_term_memory_str, soul=soul, user=user)
        logger.debug(model_config)
        agents_dic[agent_type] = Agent(model_config["base_url"],
                                       api_key,
                                       model_config["model_name"],
                                       model_config["input_type"],
                                       system_prompt,
                                       agent_type,
                                       True if agent_type == "chat" else False,
                                       model_config.get("max_context_windows"))
    global agents
    agents = agents_dic
    return agents_dic



def create_rough_schedule(schedule_description: str):
    story_agent: Agent|None = agents.get("story",None)
    if not story_agent:
        raise Exception("缺少story模型")

    rough_schedule_prompt = f"""日程描述：{schedule_description}
请根据日程描述，生成一个粗略的日程，你生成的粗略日期安排将会作为后续详细日程的参考。返回格式为：
{{
    "schedule_preferences": {{
        "weekday": {{
            "morning": 粗略早上的作息安排,
            "afternoon": 粗略下午的作息安排,
            "evening": 粗略晚上的作息安排
        }},
        "weekend": {{
            "saturday": 粗略周六的作息安排,
            "sunday": 粗略周日的作息安排
        }}
    }},
    "special_rules": {{
        "holiday": [
            {{
                "holiday_name": 假期名称,
                "arrange": 假期的粗略安排
            }}
        ],
    }}
}}
示例：
{{
    "schedule_preferences": {{
        "weekday": {{
            "morning": "9:00-12:00 通常是专注画画或处理商稿的时间，可能会有些焦虑",
            "afternoon": "14:00-18:00 可能会摸鱼看展，或者去附近的咖啡馆找灵感",
            "evening": "20:00以后 属于个人放松时间，可能会看老电影、撸猫或者听播客"
        }},
        "weekend": {{
            "saturday": "倾向于睡到自然醒。下午大概率会去逛独立书店或看画展，晚上可能会约闺蜜小聚",
            "sunday": "通常是宅家回血日，整理房间、给植物浇水，或者玩一整天主机游戏",
        }}
    }},
    "special_rules": {{
        "holiday": [
            {{
                "holiday_name": "元旦",
                "arrange": "元旦假日通常没有事情，可能会有活动或休息"
            }},
            {{
                "holiday_name": "春节",
                "arrange": "春节假期里会去亲戚家里拜年，也可能会约好友小聚"
            }}
        ],
    }}
}}
holiday需要包含的节假日包括："元旦"、"春节"、"清明节"、"劳动节"、"端午节"、"中秋节"、"国庆节"
请你严格按照指定格式返回，请勿添加格式要求以外的其他内容,不要包含任何解释、问候或前缀（如“好的”、“以下是日程”等）。
"""

    rough_schedule_str = story_agent.chat(rough_schedule_prompt)
    with open(os.path.join(setting.CONFIG_PATH, "rough_schedule.json"), "w", encoding="utf-8") as f:
        f.write(rough_schedule_str)
    logger.info(f"已生成粗略日程：{rough_schedule_str}")
    data_dict = common_util.safe_json_loads(rough_schedule_str)
    rough_schedule = RoughSchedule.model_validate(data_dict)

    return rough_schedule



    


