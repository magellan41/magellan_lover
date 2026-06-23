# magellan_lover服务

基于 FastAPI 的 AI 智能助手后端服务。
支持多轮对话、语音合成、图片生成、长期/中期/短期记忆管理、主动对话

前端项目：[magellan_lover_front_end](https://github.com/magellan41/magellan_lover_front_end)

## 环境要求

- Python >= 3.11
- MySQL 数据库


## 快速开始

### 下载依赖
```bash
   pip install -r requirements.txt
```
### 修改配置文件

复制模板文件并填入真实值：

```bash
cp config/llm_config.json.example config/llm_config.json
cp config/db.ini.example config/db.ini
cp config/env.json.example config/env.json
cp config/soul.md.example config/soul.md
cp config/user.md.example config/user.md
```

| 文件 | 说明 |
|------|------|
| `config/env.json` | 运行时变量（agent 名称、头像路径、语音、图片生成等），由系统自动维护 |
| `config/db.ini` | MySQL 数据库连接信息 |
| `config/llm_config.json` | LLM 模型配置，支持 OpenAI-like API |
| `config/soul.md` | Agent 人设 |
| `config/user.md` | 用户信息 |
| `config/chat_system_prompt.txt` | 聊天系统提示词 |
| `config/compact_system_prompt.txt` | 对话压缩系统提示词 |
| `config/memory_system_prompt.txt` | 记忆管理系统提示词 |
| `config/story_system_prompt.txt` | 状态日程管理系统提示词 |

- config/env.json
  - `last_interaction_time`为最后交互时间，由系统修改
  - `avatar_user`、`avatar_agent`为用户头像和agent头像的路径，前端页面点击头像位置修改
  - `agent_name`为前端显示的agent名称
  - `voice_enable`为是否开启语音输出功能（"true"/"false"）
  - `voice_key_type`为语音 API key 来源类型（"env" 或 "str"）
  - `voice_api_key`为语音 API key
  - `voice_generation_type`为语音合成类型（目前仅支持 minimax）
  - `character_image_path`、`character_image_url`为角色图片路径，用于生成角色自拍
  - `image_generator_platform`为图片生成平台
  - `image_generator_api_key`为图片生成 API key
  - `image_generator_model`为图片生成模型
- config/db.ini
  - 数据库配置
- config/llm_config.json
  - 注意使用支持openai like api的llm模型
  - api_key为${xxx}格式时会从环境变量中读取xxx对应的值

`platforms` 字段说明：配置可用的 LLM 平台，每个平台包含 `platform`（平台名）、`base_url`、`key_type`、`api_key`、`models`（模型列表，含 `name`、`input_type`、`max_context_windows`）

`agents` 字段说明：
- `chat` — 主聊天模型（格式：`平台名/模型名`）
- `compact` — 对话压缩模型
- `memory` — 记忆管理模型
- `story` — agent状态日程管理模型

### 启动服务
```bash
   python main.py
```


## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat/send` | POST | 发送消息 |
| `/api/chat/image` | POST | 上传对话图片（最多9张） |
| `/api/chat/stream` | GET | SSE 消息流（长连接） |
| `/api/chat/list/{min_id}` | GET | 获取聊天记录（每次100条） |
| `/api/lover/config/show/{config}` | GET | 获取伴侣配置（soul/user） |
| `/api/lover/config/set/{config}` | POST | 设置伴侣配置 |
| `/api/agent/config/get` | GET | 获取 agent LLM 配置 |
| `/api/agent/config/set` | POST | 设置 agent LLM 配置 |
| `/api/agent/env/get/{key}` | GET | 获取 agent 环境配置项 |
| `/api/agent/env/set` | POST | 设置 agent 环境配置项 |
| `/api/agent/voice/get` | GET | 获取语音合成配置 |
| `/api/agent/voice/set` | POST | 设置语音合成配置 |
| `/api/agent/schedule_description/get` | GET | 获取日程描述 |
| `/api/agent/schedule_description/set` | POST | 设置日程描述 |
| `/api/agent/image_generator/platform/get` | GET | 获取可选图片生成平台 |
| `/api/file/uploads/avatar/{owner}` | POST | 上传头像（user/agent） |
| `/api/file/uploads/common` | POST | 上传通用文件 |
| `/api/file/uploads/character_image` | POST | 上传角色图片（用于自拍生成） |
| `/api/memory/mid/list` | GET | 获取中期记忆列表 |
| `/api/memory/mid/delete` | DELETE | 批量删除中期记忆 |
| `/api/memory/long/list` | GET | 获取长期记忆列表 |
| `/api/memory/long/delete` | DELETE | 批量删除长期记忆 |

## 项目结构
```
magellan_lover/
├── api/ # FastAPI 路由
│   ├── api_chat.py # 聊天接口
│   ├── api_config.py # 配置接口
│   ├── api_file.py # 文件上传接口
│   └── api_memory.py # 记忆管理接口
├── config/ # 配置文件（含 .example 模板）
├── entity/ # 数据模型
│   ├── Chat.py # 聊天消息模型
│   ├── Dialogue.py # 对话模型
│   ├── Memory.py # 记忆模型
│   ├── Schedule.py # 日程模型
│   ├── Task.py # 任务模型
│   └── config.py # 配置模型
├── orm/ # 数据库操作层
│   ├── dialog_history_orm.py # 对话历史
│   ├── long_term_memory_orm.py # 长期记忆
│   ├── mid_term_memroy_orm.py # 中期记忆
│   ├── schedule_orm.py # 日程管理
│   ├── short_term_memory_orm.py # 短期记忆
│   └── sql_session.py # 数据库会话
├── scheduler/ # 定时任务
│   └── system_scheduler.py # 主动对话、记忆清理、日程生成
├── static/ # 静态资源
│   ├── downloads/selfie/ # 生成的自拍图片
│   ├── holiday/ # 节假日数据
│   ├── uploads/
│   │   ├── avatar/ # 用户/agent 头像
│   │   ├── character_image/ # 角色图片
│   │   └── chat_image/ # 对话图片
│   └── voice/ # 生成的语音文件
├── utils/ # 工具模块
│   ├── agent_util.py # Agent 管理
│   ├── common_util.py # 通用工具
│   ├── config_util.py # 配置工具
│   ├── env_util.py # 环境变量工具
│   ├── function_call_util.py # 函数调用工具
│   ├── holiday_util.py # 节假日工具
│   ├── llm_util.py # LLM 调用工具
│   ├── setting.py # 路径配置
│   ├── singleton.py # 单例模式
│   └── voice_generation.py # 语音合成
├── main.py # 入口
└── requirements.txt
```