# analyzer.py
"""
状态分析引擎 - 基于多维度数据推理用户状态
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .models import UserProfile, WorkingMemory, HealthGoal
from .memory import MemorySystem


class StateAnalyzer:
    """状态分析引擎"""

    def __init__(self, memory: MemorySystem):
        self.memory = memory

    def analyze(self, user_id: str, current_input: str = "") -> Dict:
        """
        综合分析用户状态

        Returns:
            {
                "physical_state": {...},
                "behavioral_state": {...},
                "psychological_state": {...},
                "contextual_state": {...},
                "overall": "good/moderate/poor",
                "insights": [...],
                "recommendations": [...]
            }
        """
        profile = self.memory.get_user_profile(user_id)
        working = self.memory.get_working_memory(user_id)

        # 1. 身体状态分析
        physical_state = self._analyze_physical(profile, working)

        # 2. 行为模式分析
        behavioral_state = self._analyze_behavior(working)

        # 3. 心理状态分析
        psychological_state = self._analyze_psychological(working, current_input)

        # 4. 情境因素分析
        contextual_state = self._analyze_context(profile, working)

        # 5. 综合分析
        overall, insights, recommendations = self._synthesize(
            physical_state, behavioral_state, psychological_state, contextual_state
        )

        # 确保返回的是简单类型
        return {
            "physical_state": {
                "activity_level": physical_state["activity_level"],
                "activity_count": physical_state["activity_count"],
                "total_exercise_minutes": physical_state["total_exercise_minutes"],
                "sleep_quality": physical_state["sleep_quality"],
                "fatigue_score": physical_state["fatigue_score"],
                "health_concerns": physical_state["health_concerns"]
            },
            "behavioral_state": {
                "consistency_score": behavioral_state["consistency_score"],
                "patterns": behavioral_state["patterns"],
                "pending_tasks": behavioral_state["pending_tasks"],
                "weekly_goals_completed": behavioral_state["weekly_goals_completed"]
            },
            "psychological_state": {
                "mood": psychological_state["mood"],
                "motivation_level": psychological_state["motivation_level"],
                "self_efficacy": psychological_state["self_efficacy"],
                "risks": psychological_state["risks"]
            },
            "contextual_state": {
                "has_active_goals": contextual_state["has_active_goals"],
                "historical_success_rate": contextual_state["historical_success_rate"],
                "preferred_exercises": contextual_state["preferred_exercises"],
                "avoided_exercises": contextual_state["avoided_exercises"]
            },
            "overall": overall,
            "insights": insights,
            "recommendations": recommendations
        }


    def _analyze_physical(self, profile: UserProfile, working: WorkingMemory) -> Dict:
        """分析身体状态"""
        # 计算活动量
        recent_activities = working.recent_exercises[-7:]  # 最近7天
        activity_count = len(recent_activities)
        total_duration = sum(a.get("duration", 0) for a in recent_activities)

        # 分析睡眠 - 确保不返回 datetime
        sleep_pattern = "unknown"
        if working.recent_sleep:
            # 确保只取数值
            sleep_hours = []
            for s in working.recent_sleep[-7:]:
                hours = s.get("hours")
                if hours is not None:
                    sleep_hours.append(float(hours) if isinstance(hours, (int, float)) else 0)

            if sleep_hours:
                avg_hours = sum(sleep_hours) / len(sleep_hours)
                if avg_hours >= 7:
                    sleep_pattern = "good"
                elif avg_hours >= 6:
                    sleep_pattern = "fair"
                else:
                    sleep_pattern = "poor"

        # 评估疲劳度
        fatigue = 0
        if activity_count > 5 and total_duration > 300:
            fatigue += 20
        if sleep_pattern == "poor":
            fatigue += 30

        return {
            "activity_level": "high" if activity_count >= 4 else "moderate" if activity_count >= 2 else "low",
            "activity_count": activity_count,
            "total_exercise_minutes": total_duration,
            "sleep_quality": sleep_pattern,
            "fatigue_score": min(fatigue, 100),
            "health_concerns": profile.health_issues[:3] if profile.health_issues else []
        }

    def _analyze_behavior(self, working: WorkingMemory) -> Dict:
        """分析行为模式"""
        # 分析一致性
        exercise_consistency = 0
        if len(working.recent_exercises) >= 4:
            # 检查是否有规律
            dates = [e.get("date") for e in working.recent_exercises[-7:]]
            unique_dates = len(set(dates))
            exercise_consistency = min(100, unique_dates * 20)

        # 识别模式
        patterns = []
        if len(working.recent_exercises) == 0 and len(working.weekly_goals) > 0:
            patterns.append("goal_behavior_gap")  # 目标与行为脱节

        return {
            "consistency_score": exercise_consistency,
            "patterns": patterns,
            "pending_tasks": len(working.pending_tasks),
            "weekly_goals_completed": sum(1 for g in working.weekly_goals if "完成" in g)
        }

    def _analyze_psychological(self, working: WorkingMemory, current_input: str) -> Dict:
        """分析心理状态"""
        # 从当前输入推断情绪
        mood = working.current_mood
        motivation = working.motivation_level or 5

        # 简单情绪关键词检测
        if current_input:
            positive_words = ["好", "棒", "开心", "成功", "坚持", "进步"]
            negative_words = ["累", "烦", "难", "放弃", "没时间", "失败"]

            for word in positive_words:
                if word in current_input:
                    motivation = min(motivation + 1, 10)
            for word in negative_words:
                if word in current_input:
                    motivation = max(motivation - 1, 1)

        # 判断风险
        risks = []
        if motivation < 4:
            risks.append("low_motivation")

        return {
            "mood": mood or "neutral",
            "motivation_level": motivation,
            "self_efficacy": motivation * 10,  # 简化
            "risks": risks
        }

    def _analyze_context(self, profile: UserProfile, working: WorkingMemory) -> Dict:
        """分析情境因素"""
        # 检查是否有活跃目标
        has_active_goals = len(profile.active_goals) > 0

        # 检查是否有历史成功经验
        success_rate = 0
        if profile.achievements:
            success_rate = min(100, len(profile.achievements) * 20)

        return {
            "has_active_goals": has_active_goals,
            "historical_success_rate": success_rate,
            "preferred_exercises": profile.exercise_preferences[:3],
            "avoided_exercises": profile.avoided_exercises[:2]
        }

    def _synthesize(self, physical: Dict, behavioral: Dict, psychological: Dict, contextual: Dict) -> Tuple[
        str, List[str], List[str]]:
        """综合所有维度，生成洞察和建议"""
        insights = []
        recommendations = []

        # 综合评分
        scores = []

        # 身体状态评分
        if physical["activity_level"] == "high":
            scores.append(80)
        elif physical["activity_level"] == "moderate":
            scores.append(50)
        else:
            scores.append(20)
            insights.append("近期运动量不足")
            recommendations.append("建议从轻度活动开始，如每天15分钟快走")

        # 睡眠评分
        if physical["sleep_quality"] == "good":
            scores.append(80)
        elif physical["sleep_quality"] == "fair":
            scores.append(50)
            insights.append("睡眠质量一般，可能影响恢复")
            recommendations.append("尝试固定作息时间，睡前减少屏幕使用")
        else:
            scores.append(20)
            insights.append("睡眠不足，需要优先改善")
            recommendations.append("建议在晚上10点后放松身心，准备入睡")

        # 动机评分
        motivation = psychological["motivation_level"]
        if motivation >= 7:
            scores.append(80)
            insights.append("当前动力充足，是开始新习惯的好时机")
        elif motivation >= 4:
            scores.append(50)
            insights.append("动力水平适中，需要一些外部激励")
            recommendations.append("可以找个运动伙伴，或设置小奖励")
        else:
            scores.append(20)
            insights.append("动力较低，需要重建信心")
            recommendations.append("建议回顾过去的成功经验，从最小目标开始")

        # 综合
        avg_score = sum(scores) / len(scores) if scores else 50
        if avg_score >= 70:
            overall = "good"
        elif avg_score >= 40:
            overall = "moderate"
        else:
            overall = "poor"

        return overall, insights, recommendations