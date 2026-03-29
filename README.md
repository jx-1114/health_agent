# 健康与健身 Agent

一个智能健康助手，具备长期记忆、自主决策和主动干预能力。

## 功能特性

- 🌤️ **天气查询**：实时获取天气，推荐运动建议
- 🍎 **饮食分析**：分析餐食营养，提供健康建议
- 📋 **运动计划**：个性化运动计划生成
- 💪 **激励系统**：智能鼓励和支持
- 🧠 **长期记忆**：记住用户偏好和历史
- ⏰ **主动提醒**：定时提醒和主动询问

## 快速开始

### 环境要求

- Python 3.9+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 为 `.env`，填入你的 API 密钥：

```env
# LLM API（用于 Agent 决策）
LLM_API_KEY=your_api_key

# 和风天气 API
QWEATHER_API_KEY=your_weather_key
QWEATHER_API_HOST=your_host

# Edamam 营养分析 API（可选，系统会降级使用本地数据库）
EDAMAM_APP_ID=your_app_id
EDAMAM_APP_KEY=your_app_key
```

### 启动服务

```bash
python run.py
```

服务启动后访问：http://127.0.0.1:8000

### 测试 API

```bash
# 健康检查
curl http://127.0.0.1:8000/api/health

# 初始化 Agent
curl -X POST http://127.0.0.1:8000/api/init \
  -H "Content-Type: application/json" \
  -d '{"user_id":"me","api_key":"your_api_key","model":"qwen-max"}'

# 发送消息
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"me","message":"武汉今天天气怎么样？"}'
```

## 项目结构

```
health_agent/
├── app/                    # 核心应用代码
│   ├── agent.py           # Agent 主控逻辑
│   ├── memory.py          # 记忆系统
│   ├── analyzer.py        # 状态分析引擎
│   ├── planner.py         # 计划生成器
│   ├── tools.py           # 外部工具集成
│   ├── scheduler.py       # 定时任务调度
│   ├── models.py          # 数据模型
│   ├── config.py          # 配置管理
│   └── main.py            # FastAPI 入口
├── static/                 # 前端静态文件
│   └── index.html         # 聊天界面
├── data/                   # 数据持久化目录
├── tests/                  # 测试脚本
├── .env                    # 环境变量
├── run.py                  # 启动脚本
└── requirements.txt        # 项目依赖
```

## API 文档

启动服务后访问：http://127.0.0.1:8000/docs

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/init` | POST | 初始化 Agent |
| `/api/chat` | POST | 发送消息 |
| `/api/checkin/{user_id}` | GET | 主动询问 |
| `/api/status/{user_id}` | GET | 获取用户状态 |

## 使用示例

### 天气查询
```
用户：武汉今天天气怎么样？
助手：📍 武汉的天气情况：
      ☁️ 天气：雾
      🌡️ 温度：15°C
      💧 湿度：88%
      💨 风速：5级
      ⚠️ 不太适合户外运动，建议在家做瑜伽或拉伸。
```

### 制定运动计划
```
用户：我想减肥
助手：好的！针对「减重」的目标，我为你制定了减重计划：
      📋 周计划
      - 周一：快走 30分钟
      - 周三：游泳 30分钟
      - 周五：慢跑 30分钟
      💡 每日建议
      - 增加蛋白质摄入
      - 每天喝够2L水
      - 晚餐在睡前3小时完成
```

### 饮食分析
```
用户：一个苹果有多少热量？
助手：📊 营养分析：
      热量：52 kcal
      蛋白质：0.3 g
      碳水：14 g
      脂肪：0.2 g
      膳食纤维：2.4 g
```

## 技术栈

- **后端框架**：FastAPI
- **LLM**：Qwen / DeepSeek
- **天气 API**：和风天气 v7
- **营养 API**：Edamam / 本地数据库
- **前端**：HTML/CSS/JavaScript

## 项目亮点

- 🧠 **三级记忆体系**：长期记忆（用户画像）、工作记忆（短期行为）、会话记忆（当前对话）
- 🔌 **工具化设计**：天气、营养、运动等能力解耦，易于扩展
- 🛡️ **降级机制**：API 异常时自动切换本地数据，保证服务可用
- ⏰ **主动干预**：定时提醒 + 状态检测，实现主动关怀
- 🌐 **中文优化**：智能城市识别，支持自然语言交互

## License

MIT

## 作者

papacito jane