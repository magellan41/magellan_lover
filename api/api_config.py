import os.path

from fastapi import APIRouter, Body

from utils import setting

import logging

from utils.agents import init_agents
from utils import env_util

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

