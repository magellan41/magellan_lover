import os
import logging

from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from utils import setting

# 初始化绝对路径
setting.init(Path(__file__).parent)

from utils import agent_util


# =============================日志配置=============================
# 全局统一配置根 Logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(setting.ROUT_PATH, "logs", "magellan_lover.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# =============================定时任务=============================
from contextlib import asynccontextmanager
from scheduler.system_scheduler import daily_schedule_task
from utils import scheduler_util


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 启动时：初始化并启动定时任务
    scheduler_util.init_scheduler()
    # 初始化每日日程表
    await daily_schedule_task()
    yield  # FastAPI 主程序运行中...

    # 2. 关闭时：优雅地关闭定时任务
    scheduler_util.stop_scheduler()


app = FastAPI(title="Magellan Lover 服务", lifespan=lifespan)
# 解决跨域（必须加，否则 Vue 访问报错）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.api_chat import router as chat_router
from api.api_config import router as config_router
from api.api_memory import router as memory_router
from api.api_file import router as file_router
from api.api_agent_work import router as agent_work_router


app.include_router(chat_router)
app.include_router(config_router)
app.include_router(memory_router)
app.include_router(file_router)
app.include_router(agent_work_router)

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=setting.STATIC_PATH), name="static")

from utils import voice_generation
# 初始化语音配置
voice_generation.init_voice_generation()

# 初始化 Agent
agent_util.init_agents()



if __name__ == "__main__":
    import uvicorn

    # 对应：uvicorn main:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )

