import asyncio
import re

from orm.dialog_history_orm import DialogueHistoryOrm
from orm.memes_orm import MemesOrm

import logging

from utils import push_util, env_util
from utils.voice_generation import voice_generation

logger = logging.getLogger(__name__)


active_connections: set = set()

dialogue_history_orm_obj = DialogueHistoryOrm()
memes_orm_obj = MemesOrm()


def text_delay(content: str) -> float:
    """
    计算文本的延时时间，单位：秒
    """
    return len(content) * 0.1

async def notify_all(response_data):
    agent_name = env_util.read_env_var("agent_name")
    if agent_name == "未找到该配置项":
        tag = "来提示啦"
    else:
        tag = agent_name
    if isinstance(response_data, str) and response_data.startswith("【ERROR】"):
        push_util.send_push_meizu(f"【错误】{tag}", response_data)
        # 报错落库
        dialogue_history_orm_obj.insert(response_data, "agent", "text")
        if active_connections:
            await asyncio.gather(*[
                conn_queue.put(response_data) for conn_queue in active_connections
            ])
        return

    # 清理文本
    pattern = r'\[flag:\s*(?P<flag>.*?)\]\[voice:\s*(?P<voice>.*?)\](?P<content>.*)'
    match = re.search(pattern, response_data,flags=re.DOTALL)
    if match:
        result = match.groupdict()
    else:
        result = {"flag": "true", "voice": "false", "content": response_data}
    flag = result["flag"] == "true" or result["flag"] == "True"
    if not flag:
        logger.debug(f"flag: {flag}, 不回复用户")
        return
    voice_flag = result["voice"] == "true" or result["voice"] == "True"
    content = result["content"]

    content = content.replace("）", ")").replace("（", "(")
    # 非语音模式下，移除所有语气词
    if not voice_flag:
        # interjection = ["(chuckle)", "(laughs)", "(sneezes)", "(coughs)", "(clear-throat)", "(groans)", "(breath)",
        #                 "(pant)", "(inhale)", "(exhale)", "(gasps)", "(sighs)", "(sniffs)", "(snorts)", "(burps)",
        #                 "(lip-smacking)", "(humming)", "(hissing)", "(emm)"]
        # pattern1 = "|".join(map(re.escape, interjection))
        pattern1 = r'\([a-zA-Z-]+\)'
        pattern2 = r'<#\d+(?:\.\d+)?#>'
        pattern = f"{pattern1}|{pattern2}"
        new_str = re.sub(pattern, "", content)
        new_str = re.sub(r'[^\S\n]+', ' ', new_str).strip()
        content = new_str
        logger.debug(f"清理后内容: {content}")

    # content_list = content.split("\n\n")
    split_pattern = r'(\n|<selfie>.*?</selfie>|<memes>.*?</memes>)'
    content_list = [part for part in re.split(split_pattern, content) if part]
    logger.debug(f"split后内容列表: {content_list}")
    for item in content_list:
        sleep_trme = 0.3
        push_content = item
        item = item.strip()
        if item == "" or item == r"\n\n" or item == r"\n" or item == r"<selfie>" or item == r"</selfie>":
            continue
        if item.startswith("<selfie>"):
            item = item.replace("<selfie>", "").replace("</selfie>", "")
            dialogue_history_orm_obj.insert(item, "agent", "image")
            item =  f"{{\"flag\": \"{"true" if flag else "false"}\", \"type\": \"image\", \"content\": \"{item}\", \"role\": \"agent\", \"duration_seconds\": 0.0}}"
            # 自拍不用添加延时
            push_content = "[自拍]"
        elif item.startswith("<memes>"):
            item = item.replace("<memes>", "").replace("</memes>", "")
            try:
                id = int(item)
                memes_obj = memes_orm_obj.select_by_id(id)
                dialogue_history_orm_obj.insert(memes_obj.url, "agent", "image")
                item = f"{{\"flag\": \"{"true" if flag else "false"}\", \"type\": \"image\", \"content\": \"{memes_obj.url}\", \"role\": \"agent\", \"duration_seconds\": 0.0}}"
                # 表情包不用添加延时
                push_content = "[表情包]"
            except Exception as e:
                logger.error(f"memes error: {e}")
                item = f"{{\"flag\": \"{"true" if flag else "false"}\", \"type\": \"text\", \"content\": \"尝试发送表情包{item}失败:{e}\", \"role\": \"agent\", \"duration_seconds\": 0.0}}"
        elif voice_flag:
            success, voice_path, duration_seconds = voice_generation(item)
            logger.debug(f"voice_generation success: {success}, voice_path: {voice_path}, duration_seconds: {duration_seconds}")
            if success:
                item = voice_path
                dialogue_history_orm_obj.insert(item, "agent", "voice", duration_seconds=duration_seconds)
                item = f"{{\"flag\": \"{"true" if flag else "false"}\", \"type\": \"voice\", \"content\": \"{item}\", \"duration_seconds\": {duration_seconds}, \"role\": \"agent\"}}"
                # 语音需要添加语音长度/2的延时
                push_content = "[语音]"
                sleep_trme += duration_seconds / 2
        # 发送文本逻辑不用修改提示内容
            else:
                # 语音合成失败，直接插入文本
                dialogue_history_orm_obj.insert(item, "agent", "text")
                push_util.send_push_meizu(tag, item)
                item = f"{{\"flag\": \"{"true" if flag else "false"}\", \"type\": \"text\", \"content\": \"{item}\", \"role\": \"agent\", \"duration_seconds\": 0.0}}"
                sleep_trme += text_delay(item)
        else:
            dialogue_history_orm_obj.insert(item, "agent", "text")
            item = f"{{\"flag\": \"{"true" if flag else "false"}\", \"type\": \"text\", \"content\": \"{item}\", \"role\": \"agent\", \"duration_seconds\": 0.0}}"
            sleep_trme += text_delay(item)

        # 将 Agent 的响应封装并推入 SSE 管道
        # await sse_push_queue.put(response_data)
        await asyncio.sleep(sleep_trme)
        if active_connections:
            await asyncio.gather(*[
                conn_queue.put(item) for conn_queue in active_connections
            ])
        push_util.send_push_meizu(tag, push_content)
