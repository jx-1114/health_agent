# app/main.py
"""
健康与健身 Agent - 主入口 (FastAPI)
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import os
import signal
import sys
from pathlib import Path

from .agent import HealthAgent
from .config import ModelConfig


# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    """对话请求"""
    user_id: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str
    message: str
    action_type: str
    suggestions: list = []
    plan: Optional[Dict] = None
    state: Optional[Dict] = None


class InitRequest(BaseModel):
    """初始化请求"""
    user_id: str
    api_key: str
    model: Optional[str] = None


# ==================== 应用初始化 ====================

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="健康与健身 Agent",
    description="智能健康助手 - 具备长期记忆、自主决策和主动干预能力的 Agent",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Agent 实例存储
agents: Dict[str, HealthAgent] = {}


def get_agent(user_id: str, api_key: str = None, model: str = None) -> HealthAgent:
    """获取或创建 Agent 实例"""
    if user_id not in agents:
        if not api_key:
            raise HTTPException(status_code=400, detail="首次使用需要提供 API 密钥")
        agents[user_id] = HealthAgent(api_key=api_key, model=model)
    return agents[user_id]


# ==================== API 端点 ====================

@app.get("/")
async def root():
    """返回前端页面"""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "健康与健身 Agent API", "version": "1.0.0"}


@app.get("/api/health")
async def health():
    """健康检查"""
    return {"status": "ok", "agents": len(agents)}


@app.post("/api/init")
async def initialize_agent(request: InitRequest):
    """初始化用户 Agent"""
    print(f"[DEBUG] 初始化 Agent: user_id={request.user_id}")
    agent = HealthAgent(api_key=request.api_key, model=request.model)
    agents[request.user_id] = agent
    return {
        "status": "success",
        "user_id": request.user_id,
        "message": "Agent 已初始化"
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """与 Agent 对话"""
    print(f"[DEBUG] 收到消息: {request.message}")

    if request.user_id not in agents:
        raise HTTPException(status_code=400, detail="请先调用 /api/init 初始化 Agent")

    agent = agents[request.user_id]

    try:
        result = agent.process_input(
            user_id=request.user_id,
            user_input=request.message,
            session_id=request.session_id
        )

        return ChatResponse(
            session_id=result["session_id"],
            message=result["message"],
            action_type=result["action_type"],
            suggestions=result.get("suggestions", []),
            plan=result.get("plan"),
            state=result.get("state")
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] chat 端点异常: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/checkin/{user_id}")
async def active_checkin(user_id: str):
    """Agent 主动询问"""
    if user_id not in agents:
        raise HTTPException(status_code=400, detail="Agent 未初始化")

    agent = agents[user_id]
    checkin = agent.active_checkin(user_id)

    if checkin:
        return checkin
    return {"message": "暂不需要主动干预"}


@app.get("/api/status/{user_id}")
async def get_status(user_id: str):
    """获取用户状态摘要"""
    if user_id not in agents:
        raise HTTPException(status_code=400, detail="Agent 未初始化")

    agent = agents[user_id]
    profile = agent.memory.get_user_profile(user_id)
    working = agent.memory.get_working_memory(user_id)

    return {
        "user_id": user_id,
        "active_goals": len(profile.active_goals),
        "completed_goals": len(profile.completed_goals),
        "weekly_exercises": len(working.recent_exercises),
        "motivation_level": working.motivation_level,
        "energy_level": working.energy_level
    }


@app.delete("/api/user/{user_id}")
async def delete_user(user_id: str):
    """删除用户数据"""
    if user_id in agents:
        agent = agents[user_id]
        if hasattr(agent, 'scheduler'):
            agent.scheduler.stop()
        del agents[user_id]
    return {"status": "deleted", "user_id": user_id}


# ==================== 信号处理 ====================

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    print("\n\n🛑 正在关闭服务...")
    for user_id, agent in agents.items():
        if hasattr(agent, 'scheduler'):
            agent.scheduler.stop()
    print("✅ 服务已安全关闭")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ==================== 启动入口 ====================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )