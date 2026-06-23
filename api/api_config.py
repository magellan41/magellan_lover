import os.path
from typing import Dict, Any

from fastapi import APIRouter, Body

from entity.config import VoiceConfig, RoughSchedule
from utils import setting, function_call_util

import logging

from utils.agent_util import init_agents, create_rough_schedule
from utils import env_util
from utils.voice_generation import init_voice_generation

logger = logging.getLogger(__name__)

# router = APIRouter()
router = APIRouter(tags=["配置接口"])

@router.get("/api/lover/config/show/{config}", summary="获取伴侣配置", description="根据配置项获取伴侣配置值")
async def show_config(config: str) -> str:
    with open(os.path.join(setting.CONFIG_PATH, f"{config}.md"), "r", encoding="utf-8") as f:
        return f.read()


@router.post("/api/lover/config/set/{config}", summary="设置伴侣配置", description="根据配置项设置伴侣配置值")
async def set_config(config: str, content: str = Body(..., description="伴侣配置值")) -> str:
    with open(os.path.join(setting.CONFIG_PATH, f"{config}.md"), "w", encoding="utf-8") as f:
        f.write(content)
    init_agents()
    return f"人格文件{config}已重设"


@router.get("/api/agent/config/get", summary="获取agent配置", description="获取agent配置项")
async def list_config() -> str:
    with open(os.path.join(setting.CONFIG_PATH, "llm_config.json"), "r", encoding="utf-8") as f:
        return f.read()

@router.post("/api/agent/config/set", summary="设置agent配置", description="设置agent配置项")
async def set_agent_config(content: str = Body(..., description="agent配置值")) -> str:
    with open(os.path.join(setting.CONFIG_PATH, "llm_config.json"), "w", encoding="utf-8") as f:
        f.write(content)
    init_agents()
    return f"agent配置已重设"

@router.get("/api/agent/env/get/{key}", summary="获取agent环境", description="获取agent环境配置项")
async def list_env_config(key: str) -> str:
    res = env_util.read_env_var(key)
    return res if res is not None else "未找到该环境配置项"

@router.post("/api/agent/env/set", summary="设置agent环境", description="设置agent环境配置项")
async def set_env_config(key: str = Body(..., description="agent环境配置项"), value: str = Body(..., description="agent环境配置值")) -> str:
    env_util.write_env_var(key, value)
    return f"agent环境配置项{key}已重设为{value}"

@router.get("/api/agent/voice/get", summary="获取agent语音环境配置", description="获取agent语音环境配置配置项voice_enable为字符串的true和false,表示是否开启语音输出功能, voice_key_type为字符串的env或str,表示语音api key的来源, voice_api_key为语音api key, voice_generation_type为语音合成类型目前只有minimax一个可选项")
async def list_voice_env_config() -> dict:
    res = env_util.read_env_vars(["voice_enable", "voice_key_type", "voice_api_key", "voice_generation_type"])
    return res



@router.post("/api/agent/voice/set", summary="设置agent语音环境", description="设置agent语音环境配置项")
async def set_voice_env_config(config: VoiceConfig = Body(..., description="agent语音环境配置项")) -> str:
    env_util.write_env_vars(["voice_enable", "voice_api_key", "voice_generation_type"],
                            [config.voice_enable, config.voice_api_key, config.voice_generation_type])
    init_voice_generation()
    return f"agent语音环境配置已重设"


@router.get("/api/agent/schedule_description/get", summary="获取agent状态日程描述", description="获取agent状态日程描述")
async def list_schedule_description() -> str:
    if not os.path.exists(os.path.join(setting.CONFIG_PATH, "schedule_description.txt")):
        return ""
    with open(os.path.join(setting.CONFIG_PATH, "schedule_description.txt"), "r", encoding="utf-8") as f:
        return f.read()



@router.post("/api/agent/schedule_description/set", summary="设置agent状态日程描述", description="设置agent状态日程描述")
async def set_schedule_description(content: str = Body(..., description="agent状态日程描述")) -> RoughSchedule:
    with open(os.path.join(setting.CONFIG_PATH, "schedule_description.txt"), "w", encoding="utf-8") as f:
        f.write(content)
    rough_schedule = create_rough_schedule(content)
    return rough_schedule


@router.get("/api/agent/image_generator/platform/get", summary="获取全部可选的图片生成器", description="获取全部可选的图片生成器")
async def list_image_generator_platform() -> list:
    return function_call_util.list_image_generator_platform()

