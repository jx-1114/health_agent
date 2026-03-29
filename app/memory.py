# memory.py - 修改 store_long_term 方法

import os
import json
import uuid
from datetime import datetime, timedelta, date  # 确保导入 date
from typing import Dict, List, Optional, Any

from .models import UserProfile, WorkingMemory, SessionContext, HealthGoal, GoalStatus
from .config import DATA_DIR


class MemorySystem:
    """统一记忆系统（简化版，使用内存存储）"""

    def __init__(self, persist_dir: str = "./data"):
        if persist_dir is None:
            persist_dir = str(DATA_DIR)
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)

        # 所有存储都使用内存 + 文件持久化
        self.session_memories: Dict[str, SessionContext] = {}
        self.working_memories: Dict[str, WorkingMemory] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.long_term_store: Dict[str, List[Dict]] = {}

        # 尝试加载已保存的数据
        self._load_data()

    def _make_serializable(self, obj):
        """将对象转换为 JSON 可序列化的格式"""
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        else:
            try:
                return str(obj)
            except:
                return None

    def _save_data(self):
        """保存数据到文件"""
        try:
            # 保存用户画像
            profiles_path = os.path.join(self.persist_dir, "profiles.json")
            profiles_data = {}
            for user_id, profile in self.user_profiles.items():
                profiles_data[user_id] = self._make_serializable(profile.to_dict())
            with open(profiles_path, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, ensure_ascii=False, indent=2)

            # 保存长期记忆
            memory_path = os.path.join(self.persist_dir, "long_term_memory.json")
            serializable_memory = self._make_serializable(self.long_term_store)
            with open(memory_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_memory, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存数据失败: {e}")

    def _load_data(self):
        """从文件加载数据"""
        try:
            # 加载用户画像
            profiles_path = os.path.join(self.persist_dir, "profiles.json")
            if os.path.exists(profiles_path):
                with open(profiles_path, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)

                for user_id, data in profiles_data.items():
                    profile = UserProfile(
                        user_id=user_id,
                        created_at=datetime.fromisoformat(data["created_at"])
                    )
                    profile.age = data.get("age")
                    profile.gender = data.get("gender")
                    profile.height = data.get("height")
                    profile.weight = data.get("weight")
                    profile.occupation = data.get("occupation")
                    profile.health_issues = data.get("health_issues", [])
                    profile.injuries = data.get("injuries", [])
                    profile.medications = data.get("medications", [])
                    profile.exercise_preferences = data.get("exercise_preferences", [])
                    profile.avoided_exercises = data.get("avoided_exercises", [])
                    profile.food_preferences = data.get("food_preferences", [])
                    profile.disliked_foods = data.get("disliked_foods", [])
                    profile.achievements = data.get("achievements", [])
                    profile.failures = data.get("failures", [])
                    profile.motivation_pattern = data.get("motivation_pattern", {})

                    self.user_profiles[user_id] = profile

            # 加载长期记忆
            memory_path = os.path.join(self.persist_dir, "long_term_memory.json")
            if os.path.exists(memory_path):
                with open(memory_path, 'r', encoding='utf-8') as f:
                    self.long_term_store = json.load(f)
            else:
                self.long_term_store = {}

        except Exception as e:
            print(f"加载数据失败: {e}")
            self.long_term_store = {}

    # ========== 长期记忆操作 ==========

    def store_long_term(self, user_id: str, memory_type: str, content: Dict):
        """存储长期记忆"""
        memory_id = f"{user_id}_{memory_type}_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().isoformat()

        # 确保 content 是可序列化的
        serializable_content = self._make_serializable(content)

        if user_id not in self.long_term_store:
            self.long_term_store[user_id] = []

        self.long_term_store[user_id].append({
            "id": memory_id,
            "type": memory_type,
            "content": serializable_content,
            "timestamp": timestamp
        })

        # 限制每个用户最多存储 1000 条记忆
        if len(self.long_term_store[user_id]) > 1000:
            self.long_term_store[user_id] = self.long_term_store[user_id][-500:]

        # 定期保存
        self._save_data()

    def query_long_term(self, user_id: str, query: str = "", memory_type: Optional[str] = None, n_results: int = 5) -> \
    List[Dict]:
        """查询长期记忆"""
        if user_id not in self.long_term_store:
            return []

        memories = self.long_term_store[user_id]

        # 按类型过滤
        if memory_type:
            memories = [m for m in memories if m.get("type") == memory_type]

        # 按时间倒序，返回最近的
        memories = sorted(memories, key=lambda x: x.get("timestamp", ""), reverse=True)

        return memories[:n_results]

    # ========== 用户画像操作 ==========

    def get_user_profile(self, user_id: str) -> UserProfile:
        """获取用户画像"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                created_at=datetime.now()
            )
            self._save_data()
        return self.user_profiles[user_id]

    def update_user_profile(self, user_id: str, updates: Dict):
        """更新用户画像"""
        profile = self.get_user_profile(user_id)
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        # 存储到长期记忆
        self.store_long_term(user_id, "profile", {
            "type": "user_profile",
            "data": {k: v for k, v in vars(profile).items() if not k.startswith("_")}
        })

        self._save_data()

    # ========== 工作记忆操作 ==========

    def get_working_memory(self, user_id: str) -> WorkingMemory:
        """获取工作记忆"""
        if user_id not in self.working_memories:
            self.working_memories[user_id] = WorkingMemory(
                user_id=user_id,
                last_updated=datetime.now()
            )

        # 检查是否需要清理过期数据
        memory = self.working_memories[user_id]
        if datetime.now() - memory.last_updated > timedelta(days=7):
            # 重置周目标
            memory.weekly_goals = []
            memory.recent_exercises = []
            memory.recent_meals = []
            memory.recent_sleep = []

        memory.last_updated = datetime.now()
        return memory

    def update_working_memory(self, user_id: str, updates: Dict):
        """更新工作记忆"""
        memory = self.get_working_memory(user_id)
        for key, value in updates.items():
            if hasattr(memory, key):
                setattr(memory, key, value)

    # ========== 会话记忆操作 ==========

    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """获取会话上下文"""
        return self.session_memories.get(session_id)

    def create_session(self, user_id: str) -> SessionContext:
        """创建新会话"""
        session_id = uuid.uuid4().hex[:16]
        session = SessionContext(
            user_id=user_id,
            session_id=session_id,
            created_at=datetime.now()
        )
        self.session_memories[session_id] = session
        return session

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到会话"""
        session = self.get_session(session_id)
        if session:
            session.messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

    def close_session(self, session_id: str):
        """关闭会话"""
        if session_id in self.session_memories:
            # 将关键信息存入工作记忆
            session = self.session_memories[session_id]
            if session.current_goal:
                working = self.get_working_memory(session.user_id)
                if session.current_goal not in working.weekly_goals:
                    working.weekly_goals.append(session.current_goal)

            del self.session_memories[session_id]

    # ========== 目标管理 ==========

    def add_goal(self, user_id: str, goal: HealthGoal) -> HealthGoal:
        """添加新目标"""
        profile = self.get_user_profile(user_id)
        profile.active_goals.append(goal)

        # 使用 to_dict 方法并确保可序列化
        goal_dict = goal.to_dict()
        serializable_goal = self._make_serializable(goal_dict)

        self.store_long_term(user_id, "goal", {
            "type": "active_goal",
            "goal_id": goal.id,
            "goal_data": serializable_goal
        })

        self._save_data()
        return goal

    def update_goal_progress(self, user_id: str, goal_id: str, progress: float):
        """更新目标进度"""
        profile = self.get_user_profile(user_id)
        for goal in profile.active_goals:
            if goal.id == goal_id:
                goal.progress = progress
                if progress >= 100:
                    goal.status = GoalStatus.COMPLETED
                    profile.completed_goals.append(goal)
                    profile.active_goals.remove(goal)

                    # 记录成就
                    profile.achievements.append({
                        "goal_id": goal_id,
                        "type": goal.type,
                        "target": goal.target,
                        "completed_at": datetime.now().isoformat(),
                        "strategies": goal.strategies
                    })
                break

        self._save_data()