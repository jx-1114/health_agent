# models.py
"""
健康与健身 Agent 数据模型
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from enum import Enum
import json


# 自定义 JSON 编码器，处理 date 和 datetime 对象
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


def to_json_serializable(obj):
    """将对象转换为 JSON 可序列化的格式"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, list):
        return [to_json_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    if hasattr(obj, '__dict__'):
        return to_json_serializable(obj.__dict__)
    return obj


class GoalStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ActionType(Enum):
    SUGGEST = "suggest"
    REMIND = "remind"
    PLAN = "plan"
    MOTIVATE = "motivate"
    ASK = "ask"
    ANALYZE = "analyze"


@dataclass
class HealthGoal:
    """健康目标"""
    id: str
    type: str
    target: str
    start_date: date
    end_date: Optional[date] = None
    status: GoalStatus = GoalStatus.ACTIVE
    progress: float = 0.0
    milestones: List[str] = field(default_factory=list)
    obstacles: List[str] = field(default_factory=list)
    strategies: List[str] = field(default_factory=list)

    def to_dict(self):
        """转换为字典，处理日期对象"""
        return {
            "id": self.id,
            "type": self.type,
            "target": self.target,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status.value,
            "progress": self.progress,
            "milestones": self.milestones,
            "obstacles": self.obstacles,
            "strategies": self.strategies
        }


@dataclass
class UserProfile:
    """用户画像（长期记忆）"""
    user_id: str
    created_at: datetime

    # 基本信息
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    occupation: Optional[str] = None

    # 健康历史
    health_issues: List[str] = field(default_factory=list)
    injuries: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)

    # 偏好
    exercise_preferences: List[str] = field(default_factory=list)
    avoided_exercises: List[str] = field(default_factory=list)
    food_preferences: List[str] = field(default_factory=list)
    disliked_foods: List[str] = field(default_factory=list)

    # 历史成就
    achievements: List[Dict] = field(default_factory=list)
    failures: List[Dict] = field(default_factory=list)

    # 激励模式
    motivation_pattern: Dict[str, Any] = field(default_factory=dict)

    # 当前活跃目标
    active_goals: List[HealthGoal] = field(default_factory=list)
    completed_goals: List[HealthGoal] = field(default_factory=list)

    def to_dict(self):
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "age": self.age,
            "gender": self.gender,
            "height": self.height,
            "weight": self.weight,
            "occupation": self.occupation,
            "health_issues": self.health_issues,
            "injuries": self.injuries,
            "medications": self.medications,
            "exercise_preferences": self.exercise_preferences,
            "avoided_exercises": self.avoided_exercises,
            "food_preferences": self.food_preferences,
            "disliked_foods": self.disliked_foods,
            "achievements": self.achievements,
            "failures": self.failures,
            "motivation_pattern": self.motivation_pattern,
            "active_goals": [g.to_dict() for g in self.active_goals],
            "completed_goals": [g.to_dict() for g in self.completed_goals]
        }


@dataclass
class WorkingMemory:
    """工作记忆（短期目标与行为）"""
    user_id: str
    last_updated: datetime

    # 本周目标
    weekly_goals: List[str] = field(default_factory=list)

    # 近期行为
    recent_exercises: List[Dict] = field(default_factory=list)
    recent_meals: List[Dict] = field(default_factory=list)
    recent_sleep: List[Dict] = field(default_factory=list)

    # 待办事项
    pending_tasks: List[str] = field(default_factory=list)

    # 当前状态
    current_mood: Optional[str] = None
    energy_level: Optional[int] = None
    motivation_level: Optional[int] = None


@dataclass
class SessionContext:
    """短期记忆（当前会话）"""
    user_id: str
    session_id: str
    created_at: datetime

    messages: List[Dict] = field(default_factory=list)
    current_goal: Optional[str] = None
    pending_questions: List[str] = field(default_factory=list)
    last_intent: Optional[str] = None
    last_state: Optional[str] = None


@dataclass
class AgentAction:
    """Agent 决策结果"""
    action_type: ActionType
    content: str
    reasoning: str
    tool_calls: List[Dict] = field(default_factory=list)
    confidence: float = 0.0