# app/agent.py
"""健康与健身 Agent - 主控 Agent"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
import json
import uuid
from enum import Enum
import re

from .models import (
    UserProfile, WorkingMemory, SessionContext,
    HealthGoal, AgentAction, ActionType, GoalStatus
)
from .memory import MemorySystem
from .analyzer import StateAnalyzer
from .planner import PlanGenerator
from .tools import (
    ExercisePlanner, NutritionAnalyzer, ProgressTracker,
    ReminderScheduler, WeatherChecker, Motivator
)
from .config import AgentConfig, ModelConfig, APIConfig

# 中国主要城市列表（用于天气查询）
CHINA_CITIES = [
    "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京", "西安", "重庆",
    "天津", "苏州", "长沙", "郑州", "青岛", "大连", "厦门", "昆明", "沈阳", "长春",
    "哈尔滨", "济南", "福州", "合肥", "南昌", "南宁", "贵阳", "兰州", "银川", "西宁",
    "呼和浩特", "乌鲁木齐", "拉萨", "海口", "三亚"
]


def extract_city(user_message: str) -> str:
    """从用户消息中智能提取城市名"""
    # 方法1：城市列表匹配
    for city in CHINA_CITIES:
        if city in user_message:
            return city

    # 方法2：正则匹配
    patterns = [
        r'([\u4e00-\u9fa5]{2,3})市',
        r'([\u4e00-\u9fa5]{2,3})天气',
        r'([\u4e00-\u9fa5]{2,3})气温',
        r'([\u4e00-\u9fa5]{2,3})今天',
    ]

    for pattern in patterns:
        match = re.search(pattern, user_message)
        if match:
            city = match.group(1)
            if city in CHINA_CITIES or len(city) == 2:
                return city

    return None

class HealthAgent:
    """健康与健身 Agent 主控类"""

    def __init__(self, api_key: str, model: str = None):
        """
        初始化 Agent

        Args:
            api_key: LLM API 密钥
            model: 模型名称
        """
        self.api_key = api_key
        self.model = model or ModelConfig.DEFAULT_MODEL

        # 初始化组件
        self.memory = MemorySystem()
        self.analyzer = StateAnalyzer(self.memory)
        self.planner = PlanGenerator(self.memory)

        # 初始化工具（使用已导入的类）
        self.exercise_planner = ExercisePlanner()
        self.nutrition_analyzer = NutritionAnalyzer()
        self.progress_tracker = ProgressTracker()
        self.reminder_scheduler = ReminderScheduler()
        self.weather_checker = WeatherChecker()
        self.motivator = Motivator()

        # 初始化运动数据库
        from .planner import ExerciseDatabase
        self.exercise_db = ExerciseDatabase()

        # 初始化通知调度器
        from .scheduler import NotificationScheduler
        self.scheduler = NotificationScheduler(self)

        # 配置 API（直接使用已导入的类）
        if APIConfig.QWEATHER_API_KEY and APIConfig.QWEATHER_API_HOST:
            WeatherChecker.QWEATHER_API_KEY = APIConfig.QWEATHER_API_KEY
            WeatherChecker.API_HOST = APIConfig.QWEATHER_API_HOST
            print(f"[INFO] 天气 API 已配置: Host={APIConfig.QWEATHER_API_HOST}")

        if APIConfig.EDAMAM_APP_ID and APIConfig.EDAMAM_APP_KEY:
            NutritionAnalyzer.EDAMAM_APP_ID = APIConfig.EDAMAM_APP_ID
            NutritionAnalyzer.EDAMAM_APP_KEY = APIConfig.EDAMAM_APP_KEY

        if APIConfig.EMAIL_SENDER:
            from .tools import NotificationSender
            NotificationSender.EMAIL_CONFIG["sender_email"] = APIConfig.EMAIL_SENDER
            NotificationSender.EMAIL_CONFIG["sender_password"] = APIConfig.EMAIL_PASSWORD

        if APIConfig.WECHAT_WEBHOOK:
            from .tools import NotificationSender
            NotificationSender.WECHAT_WEBHOOK = APIConfig.WECHAT_WEBHOOK

        # 启动调度器
        self.scheduler.start()

    def process_input(self, user_id: str, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """
        处理用户输入，返回 Agent 响应
        """
        # 1. 获取或创建会话
        if not session_id:
            session = self.memory.create_session(user_id)
            session_id = session.session_id
        else:
            session = self.memory.get_session(session_id)
            if not session:
                session = self.memory.create_session(user_id)
                session_id = session.session_id

        # 2. 保存用户消息
        self.memory.add_message(session_id, "user", user_input)

        # 3. 分析用户状态
        state = self.analyzer.analyze(user_id, user_input)

        # 4. 理解意图
        intent = self._understand_intent(user_input, state)
        session.last_intent = intent

        # 5. 获取上下文
        profile = self.memory.get_user_profile(user_id)
        working = self.memory.get_working_memory(user_id)

        # 6. Agent 决策循环
        action = self._decide_action(user_id, user_input, intent, state, profile, working)

        # 7. 执行动作
        response = self._execute_action(user_id, action, state, profile)

        # 8. 保存响应
        self.memory.add_message(session_id, "assistant", response.get("message", ""))

        # 9. 更新工作记忆
        self._update_working_memory(user_id, intent, action)

        # 10. 构建返回结果并确保可序列化
        result = {
            "session_id": session_id,
            "message": response.get("message", ""),
            "action_type": action.action_type.value if hasattr(action.action_type, 'value') else str(
                action.action_type),
            "suggestions": response.get("suggestions", []),
            "plan": response.get("plan"),
            "state": state
        }

        # 递归转换所有不可序列化的对象
        return self._make_json_serializable(result)

    def _make_json_serializable(self, obj):
        """递归地将对象转换为 JSON 可序列化的格式"""
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dict__'):
            return self._make_json_serializable(obj.__dict__)
        else:
            # 尝试转换为字符串
            try:
                return str(obj)
            except:
                return None

    def _understand_intent(self, user_input: str, state: Dict) -> str:
        """
        理解用户意图
        """
        intents = []

        # 关键词匹配
        intent_keywords = {
            "goal": ["目标", "想", "希望", "打算", "计划"],
            "progress": ["进度", "怎么样", "如何", "进展"],
            "plan": ["计划", "安排", "怎么练", "做什么"],
            "advice": ["建议", "推荐", "怎么办", "怎么", "如何"],
            "log": ["今天", "记录", "做了", "完成了"],
            "motivation": ["坚持", "动力", "鼓励", "加油"],
            "question": ["?", "？", "吗", "呢"]
        }

        for intent, keywords in intent_keywords.items():
            for kw in keywords:
                if kw in user_input:
                    intents.append(intent)
                    break

        # 默认意图
        if not intents:
            return "chat"

        return intents[0]


    def _decide_action(self, user_id: str, user_input: str, intent: str,
                       state: Dict, profile: UserProfile, working: WorkingMemory) -> AgentAction:
        """
        Agent 决策核心 - 决定下一步行动
        """
        # 1. 优先检查天气查询
        weather_keywords = ["天气", "气温", "温度", "下雨", "晴天", "刮风", "预报", "今天...天气"]
        for kw in weather_keywords:
            if kw in user_input:
                return AgentAction(
                    action_type=ActionType.SUGGEST,
                    content=user_input,
                    reasoning="用户查询天气",
                    confidence=0.95
                )

        # 2. 优先检查睡眠问题
        sleep_keywords = ["睡不着", "失眠", "睡眠", "睡不好", "入睡", "熬夜", "做梦"]
        for kw in sleep_keywords:
            if kw in user_input:
                return AgentAction(
                    action_type=ActionType.SUGGEST,
                    content=user_input,
                    reasoning="用户有睡眠问题",
                    confidence=0.95
                )

        # 3. 检查饮食问题
        diet_keywords = ["吃", "喝", "饿", "饱", "零食", "晚餐", "早餐", "午餐", "宵夜"]
        for kw in diet_keywords:
            if kw in user_input and any(q in user_input for q in ["怎么办", "怎么", "如何", "吗"]):
                return AgentAction(
                    action_type=ActionType.SUGGEST,
                    content=user_input,
                    reasoning="用户有饮食问题",
                    confidence=0.9
                )

        # 4. 检查负面情绪
        negative_keywords = ["好辛苦", "不想", "放弃", "坚持不了", "好累", "太难", "算了", "没意思", "不想动"]
        for kw in negative_keywords:
            if kw in user_input:
                return AgentAction(
                    action_type=ActionType.MOTIVATE,
                    content=user_input,
                    reasoning="用户表达负面情绪，需要鼓励和支持",
                    confidence=0.95
                )

        # 5. 检查进度查询
        progress_keywords = ["进度", "怎么样", "如何", "进展", "结果", "成绩", "效果"]
        for kw in progress_keywords:
            if kw in user_input and "天气" not in user_input:
                return AgentAction(
                    action_type=ActionType.ANALYZE,
                    content=user_input,
                    reasoning="用户询问进度",
                    confidence=0.9
                )

        # 6. 检查目标设定
        goal_keywords = ["想", "希望", "打算", "计划", "目标", "减肥", "增肌", "瘦", "锻炼", "运动"]
        for kw in goal_keywords:
            if kw in user_input:
                return AgentAction(
                    action_type=ActionType.PLAN,
                    content=user_input,
                    reasoning="用户表达了设定目标的意图",
                    confidence=0.9
                )

        # 7. 默认：友好回应
        return AgentAction(
            action_type=ActionType.ASK,
            content=user_input,
            reasoning="默认聊天模式",
            confidence=0.7
        )

    def _execute_action(self, user_id: str, action: AgentAction,
                        state: Dict, profile: UserProfile) -> Dict[str, Any]:
        """
        执行决策的动作
        """
        if action.action_type == ActionType.PLAN:
            return self._execute_plan(user_id, action, state, profile)

        elif action.action_type == ActionType.SUGGEST:
            return self._execute_suggest(user_id, action, state, profile)

        elif action.action_type == ActionType.MOTIVATE:
            return self._execute_motivate(user_id, action, state, profile)

        elif action.action_type == ActionType.ANALYZE:
            return self._execute_analyze(user_id, action, state, profile)

        else:
            return self._execute_chat(user_id, action, state, profile)


    def _execute_plan(self, user_id: str, action: AgentAction,
                      state: Dict, profile: UserProfile) -> Dict[str, Any]:
        """执行计划生成 - 根据用户输入生成个性化计划"""

        # 从 action.content 获取用户原始消息
        user_message = action.content

        # 解析用户目标
        goal_type, goal_target = self._parse_goal(user_message)

        # 创建个性化目标
        goal = HealthGoal(
            id=uuid.uuid4().hex[:8],
            type=goal_type,
            target=goal_target,
            start_date=datetime.now().date(),
            status=GoalStatus.ACTIVE
        )

        # 根据目标类型生成计划
        plan = self.planner.generate_plan(user_id, goal, profile, user_message)

        # 保存目标
        self.memory.add_goal(user_id, goal)

        # 生成个性化响应 - 直接调用 _generate_plan_response
        response_message = self._generate_plan_response(goal, plan)

        return {
            "message": response_message,
            "plan": plan,
            "suggestions": plan.get("daily_suggestions", [])
        }

    def _parse_goal(self, user_message: str) -> tuple:
        """解析用户消息，提取目标类型和具体目标"""
        goal_type = "保持健康"
        goal_target = "建立健康习惯"

        # 目标类型关键词
        goal_keywords = {
            "减重": ["减肥", "减重", "瘦身", "减脂", "轻了", "瘦下来"],
            "增肌": ["增肌", "肌肉", "强壮", "力量", "健身"],
            "提升耐力": ["耐力", "跑步", "体能", "心肺"],
            "改善睡眠": ["睡眠", "失眠", "入睡", "熬夜"],
            "减压放松": ["压力", "放松", "减压", "焦虑", "紧张"]
        }

        # 提取目标类型
        for g_type, keywords in goal_keywords.items():
            for kw in keywords:
                if kw in user_message:
                    goal_type = g_type
                    break
            if goal_type != "保持健康":
                break

        # 提取具体目标（如体重数字）
        import re
        weight_match = re.search(r'(\d+)斤', user_message)
        if weight_match:
            target_weight = weight_match.group(1)
            goal_target = f"减到{target_weight}斤"
        elif "80斤" in user_message:
            goal_target = "减到80斤"
        elif "睡眠" in user_message:
            goal_target = "改善睡眠质量"
        elif "吃" in user_message:
            goal_target = "改善饮食习惯"
        else:
            goal_target = user_message[:50] if len(user_message) < 50 else user_message[:50] + "..."

        return goal_type, goal_target

    def _execute_suggest(self, user_id: str, action: AgentAction,
                         state: Dict, profile: UserProfile) -> Dict[str, Any]:
        """执行建议生成"""

        user_message = action.content

        # 1. 天气查询
        if "天气" in user_message or "气温" in user_message:
            # 智能提取城市
            city = extract_city(user_message)

            if not city:
                city = "北京"  # 默认城市
                print(f"[INFO] 未识别到城市，使用默认: {city}")

            print(f"[DEBUG] 查询城市: {city}")

            # 获取天气
            weather = self.weather_checker.get_weather(city)

            message = f"📍 {weather['city']}的天气情况：\n\n"
            message += f"☁️ 天气：{weather['condition']}\n"
            message += f"🌡️ 温度：{weather['temperature']}°C\n"
            message += f"💧 湿度：{weather['humidity']}%\n"
            message += f"💨 风速：{weather['wind_speed']}级\n\n"

            if weather['suitable_for_outdoor']:
                message += "✅ 适合户外运动！建议去公园散步或慢跑。"
            else:
                message += "⚠️ 不太适合户外运动，建议在家做瑜伽或拉伸。"

            return {
                "message": message,
                "suggestions": ["出门注意防晒", "记得补充水分"]
            }

        # 2. 睡眠问题
        if "睡不着" in user_message or "失眠" in user_message or "睡不好" in user_message:
            message = """改善睡眠的小技巧：

    1. 🌙 **固定作息**：每天同一时间上床和起床
    2. 📱 **睡前远离屏幕**：睡前一小时不看手机
    3. 🧘 **放松身心**：深呼吸、轻拉伸、温水泡脚
    4. ☕ **注意饮食**：下午3点后不喝咖啡/茶
    5. 🌡️ **创造环境**：保持卧室黑暗、安静、凉爽

    今晚想试试哪个方法？"""

            return {
                "message": message,
                "suggestions": ["固定作息时间", "睡前放松练习", "减少咖啡因摄入"]
            }

        # 3. 饮食问题
        if "吃" in user_message and ("晚上" in user_message or "怎么办" in user_message):
            message = """晚上想吃东西是很常见的！这里有几个建议：

    1. 🍎 **识别原因**：是真的饿还是情绪性进食？
    2. 🥤 **先喝杯水**：很多时候渴被误认为是饿
    3. 🥒 **选择健康零食**：黄瓜、小番茄、无糖酸奶
    4. ⏰ **调整晚餐**：晚餐可以适当增加蛋白质，增加饱腹感
    5. 😴 **早点睡**：熬夜容易增加食欲

    你觉得自己是哪种情况呢？"""

            return {
                "message": message,
                "suggestions": ["记录饥饿感", "准备健康零食", "调整晚餐时间"]
            }

        # 4. 通用建议（基于状态分析）
        suggestions = []
        if state["physical_state"]["activity_level"] == "low":
            suggestions.append("建议每天散步15分钟，可以从今天开始")
        if state["physical_state"]["sleep_quality"] == "poor":
            suggestions.append("尝试固定作息，睡前1小时关闭电子设备")
        if state["psychological_state"]["motivation_level"] < 5:
            suggestions.append("给自己设定小目标，完成后奖励自己")

        if not suggestions:
            suggestions = ["保持目前的良好状态，持续关注身体信号"]

        message = f"根据你的情况，我有以下建议：\n- " + "\n- ".join(suggestions)

        return {
            "message": message,
            "suggestions": suggestions
        }

    def _execute_motivate(self, user_id: str, action: AgentAction,
                          state: Dict, profile: UserProfile) -> Dict[str, Any]:
        """执行激励生成 - 根据用户状态和输入生成个性化鼓励"""

        user_message = action.content
        working = self.memory.get_working_memory(user_id)

        # 根据用户消息生成针对性的鼓励
        if "辛苦" in user_message or "累" in user_message:
            message = """我理解你的感受，坚持健康生活方式确实不容易。🌟

    但请记住：
    • 你已经迈出了最重要的一步——开始行动
    • 不需要追求完美，每天进步一点点就很好
    • 累了就休息一下，这不是放弃，而是调整节奏

    要不要我帮你制定一个更轻松的计划？我们可以从每天15分钟开始，你觉得怎么样？"""

            suggestions = ["允许自己休息", "从更小的目标开始", "记录小进步给自己信心"]

        elif "不想" in user_message or "放弃" in user_message:
            message = """听到你这么说，我有点担心。💙

    改变习惯确实不容易，每个人都会有想放弃的时候。但请回想一下：
    • 当初为什么想要开始？
    • 这段时间你已经有了哪些进步？

    也许现在的计划对你来说太严格了？我们可以一起调整，让计划更适合你的节奏。要不要聊聊具体哪里让你觉得辛苦？"""

            suggestions = ["回顾最初的目标", "调整计划强度", "找个运动伙伴一起"]

        elif "怎么办" in user_message:
            message = """别着急，我们一起来想办法！🤔

    根据你的情况，我建议：
    • 先分析一下具体是什么让你觉得困难
    • 我们可以把大目标拆分成小步骤
    • 找到适合你的节奏很重要

    能具体说说遇到了什么问题吗？"""

            suggestions = ["记录困难点", "寻求专业指导", "给自己小奖励"]

        else:
            # 通用鼓励
            user_name = profile.user_id[:4] if profile.user_id else "朋友"
            progress = len(working.recent_exercises) * 10
            message = self.motivator.generate_message(user_name, "", min(progress, 100))
            suggestions = ["相信自己，你可以的", "一步一个脚印", "今天比昨天进步一点点"]

        return {
            "message": message,
            "suggestions": suggestions
        }

    def _execute_analyze(self, user_id: str, action: AgentAction,
                         state: Dict, profile: UserProfile) -> Dict[str, Any]:
        """执行分析 - 提供进度摘要"""

        working = self.memory.get_working_memory(user_id)

        # 获取真实数据
        exercise_count = len(working.recent_exercises)
        total_minutes = sum(e.get("duration", 0) for e in working.recent_exercises)

        if exercise_count == 0:
            message = "你还没有记录任何运动哦！要不要从今天开始？我可以帮你制定一个简单的计划。"
            suggestions = ["每天散步15分钟", "记录第一次运动", "设定一个小目标"]
        elif exercise_count < 3:
            message = f"近期你完成了{exercise_count}次运动，共计{total_minutes}分钟。\n\n继续加油！每周保持3-4次效果更好。"
            suggestions = ["增加运动频率", "尝试不同类型的运动", "找个运动伙伴"]
        else:
            message = f"太棒了！近期你完成了{exercise_count}次运动，共计{total_minutes}分钟。\n\n坚持得很好！继续保持！"
            suggestions = ["尝试挑战更高强度", "记录饮食", "分享你的进步"]

        return {
            "message": message,
            "suggestions": suggestions
        }

    def _execute_chat(self, user_id: str, action: AgentAction,
                      state: Dict, profile: UserProfile) -> Dict[str, Any]:
        """执行聊天响应"""
        # 简单回应的智能体版本，实际可调用 LLM
        responses = [
            "听起来不错！想聊聊你的健康目标吗？",
            "最近感觉怎么样？",
            "需要我帮你规划运动或饮食吗？",
            "有想分享的健康进展吗？"
        ]

        import random
        message = random.choice(responses)

        return {
            "message": message,
            "suggestions": []
        }

    def _generate_plan_response(self, goal: HealthGoal, plan: Dict) -> str:
        """生成计划的自然语言响应"""

        # 根据目标类型定制响应
        if "减重" in goal.type or "减" in goal.target:
            response = f"好的！针对「{goal.target}」的目标，我为你制定了减重计划：\n\n"
        elif "增肌" in goal.type:
            response = f"收到！针对「{goal.target}」的目标，我为你制定了增肌计划：\n\n"
        elif "睡眠" in goal.type:
            response = f"明白了！针对「{goal.target}」的问题，我为你制定了改善睡眠的计划：\n\n"
        elif "压力" in goal.type or "放松" in goal.type:
            response = f"好的，我来帮你减压！针对「{goal.target}」的需求，我制定了放松计划：\n\n"
        else:
            response = f"针对「{goal.target}」的目标，我为你制定了健康计划：\n\n"

        # 添加周计划
        if "weekly_plan" in plan:
            response += "📋 **周计划**\n"
            for item in plan["weekly_plan"][:3]:
                if isinstance(item, dict):
                    if "day" in item and "activity" in item:
                        response += f"- {item['day']}: {item['activity']}\n"
                    elif "day" in item and "action" in item:
                        response += f"- {item['day']}: {item['action']} ({item.get('time', '')})\n"
                    elif "day" in item and "focus" in item:
                        response += f"- {item['day']}: {item['focus']}训练 - {', '.join(item.get('exercises', []))}\n"

        # 添加每日建议
        if "daily_suggestions" in plan:
            response += "\n💡 **每日建议**\n"
            for tip in plan["daily_suggestions"][:3]:
                response += f"- {tip}\n"

        response += "\n你想从哪一天开始？我可以帮你调整。"

        return response

    def _update_working_memory(self, user_id: str, intent: str, action: AgentAction):
        """更新工作记忆"""
        working = self.memory.get_working_memory(user_id)

        # 更新最近意图
        # 实际应用中可存储更多历史

        # 如果用户完成了活动，记录
        if intent == "log":
            # 简化处理
            pass

        self.memory.update_working_memory(user_id, {})

    def active_checkin(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        主动询问 - Agent 主动发起的交互

        Returns:
            主动询问的消息，如果没有需要则返回 None
        """
        profile = self.memory.get_user_profile(user_id)
        working = self.memory.get_working_memory(user_id)
        state = self.analyzer.analyze(user_id)

        # 检查是否需要主动干预
        if state["psychological_state"]["motivation_level"] < 4:
            return {
                "message": "最近感觉怎么样？需要聊聊或者一起制定个轻松的小目标吗？",
                "action_type": "checkin",
                "reason": "用户动机较低"
            }

        if state["physical_state"]["activity_level"] == "low":
            return {
                "message": "今天还没有活动哦，要不要一起做个5分钟拉伸？",
                "action_type": "suggestion",
                "reason": "活动量不足"
            }

        if len(working.weekly_goals) > 0 and state["psychological_state"]["motivation_level"] > 6:
            return {
                "message": f"本周目标完成得怎么样？需要调整吗？",
                "action_type": "follow_up",
                "reason": "目标跟踪"
            }

        return None