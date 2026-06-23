# magellan_lover服务

基于 FastAPI 的 AI 智能助手后端服务，支持多轮对话、语音合成、长期/中期/短期记忆管理

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
| `config/env.json` | 运行时变量（agent 名称、头像路径等），由系统自动维护 |
| `config/db.ini` | MySQL 数据库连接信息 |
| `config/llm_config.json` | LLM 模型配置，支持 OpenAI-like API |
| `config/soul.md` | Agent 人设 |
| `config/user.md` | 用户信息 |

- config/env.json
  - `last_interaction_time`为最后交互时间，由系统修改
  - `avatar_user`、`avatar_agent`为用户头像和agent头像的路径，前端页面点击头像位置修改
  - `agent_name`为前端显示的agent名称
- config/db.ini
  - 数据库配置
- config/llm_config.json
  - 注意使用支持openai like api的llm模型
  - api_key为${xxx}格式时会从环境变量中读取xxx对应的值

`agents` 字段说明：
- `chat` — 主聊天模型
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
| `/api/chat/stream` | GET | SSE 消息流（长连接） |
| `/api/chat/list/{min_id}` | GET | 获取聊天记录 |
| `/api/config/...` | — | 配置相关接口 |
| `/api/file/...` | — | 文件上传相关接口 |
| `/api/memory/...` | — | 记忆管理接口 |

## 项目结构
```
magellan_lover/
├── api/ # FastAPI 路由
├── config/ # 配置文件（含 .example 模板）
├── entity/ # 数据模型
├── orm/ # 数据库操作层
├── scheduler/ # 定时任务
├── static/voice/ # 生成的语音文件
├── uploads/avatar/ # 用户上传头像
├── utils/ # 工具模块
├── main.py # 入口
└── requirements.txt
```

