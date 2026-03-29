# planner.py
"""
计划生成器 - 动态生成个性化健康计划
"""
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .models import UserProfile, WorkingMemory, HealthGoal, GoalStatus
from .memory import MemorySystem
from .config import ToolConfig
import json
from pathlib import Path


class ExerciseDatabase:
    """运动数据库"""

    # 完整的运动库
    EXERCISES = {
        # 有氧运动
        "cardio": {
            "初级": ["快走 20分钟", "慢跑 15分钟", "游泳 20分钟", "骑车 30分钟", "椭圆机 20分钟"],
            "中级": ["慢跑 30分钟", "游泳 40分钟", "跳绳 15分钟", "动感单车 30分钟", "划船机 20分钟"],
            "高级": ["长跑 5公里", "高强度间歇 20分钟", "游泳 1000米", "骑行 15公里"]
        },
        # 力量训练
        "strength": {
            "上肢": ["俯卧撑 3x10", "哑铃弯举 3x12", "引体向上 3x5", "肩推 3x10", "划船 3x12"],
            "下肢": ["深蹲 3x12", "弓步蹲 3x10", "腿举 3x12", "臀桥 3x15", "提踵 3x20"],
            "核心": ["平板支撑 60秒", "卷腹 3x15", "俄罗斯转体 3x20", "仰卧抬腿 3x12", "鸟狗式 3x10"]
        },
        # 瑜伽/拉伸
        "yoga": {
            "放松": ["猫牛式", "婴儿式", "下犬式", "蝴蝶式", "快乐婴儿式"],
            "力量": ["平板式", "战士一式", "战士二式", "三角式", "树式"],
            "平衡": ["山式", "舞王式", "半月式", "鹰式"]
        },
        # 高强度间歇
        "hiit": {
            "全身": ["波比跳", "高抬腿", "开合跳", "登山跑", "深蹲跳"],
            "燃脂": ["跳绳", "冲刺跑", "滑冰跳", "侧向移动"]
        },
        # 户外活动
        "outdoor": {
            "休闲": ["徒步 5公里", "公园散步 40分钟", "骑自行车 10公里", "划船 1小时"],
            "挑战": ["爬山 2小时", "越野跑 5公里", "露营徒步"]
        }
    }

    # 计划模板
    PLAN_TEMPLATES = {
        "减重": {
            "description": "高效燃脂计划",
            "weekly_structure": [
                {"day": "周一", "type": "cardio", "level": "中级", "duration": 30},
                {"day": "周二", "type": "strength", "focus": "全身", "duration": 20},
                {"day": "周三", "type": "cardio", "level": "初级", "duration": 30},
                {"day": "周四", "type": "strength", "focus": "核心", "duration": 15},
                {"day": "周五", "type": "hiit", "duration": 15},
                {"day": "周六", "type": "outdoor", "duration": 60},
                {"day": "周日", "type": "yoga", "focus": "放松", "duration": 30}
            ],
            "diet_tips": [
                "每天摄入热量控制在基础代谢的80%",
                "每餐蔬菜占一半，蛋白质占1/4",
                "多喝水，每天2L以上",
                "晚餐在睡前3小时完成"
            ]
        },
        "增肌": {
            "description": "增肌塑形计划",
            "weekly_structure": [
                {"day": "周一", "type": "strength", "focus": "上肢", "duration": 45},
                {"day": "周二", "type": "cardio", "level": "初级", "duration": 20},
                {"day": "周三", "type": "strength", "focus": "下肢", "duration": 45},
                {"day": "周四", "type": "rest", "duration": 0},
                {"day": "周五", "type": "strength", "focus": "全身", "duration": 40},
                {"day": "周六", "type": "strength", "focus": "核心", "duration": 30},
                {"day": "周日", "type": "yoga", "focus": "拉伸", "duration": 30}
            ],
            "diet_tips": [
                "每天摄入1.6-2.2g/kg蛋白质",
                "运动后30分钟内补充蛋白质",
                "保证充足碳水供能",
                "睡眠7-9小时促进恢复"
            ]
        },
        "改善睡眠": {
            "description": "助眠放松计划",
            "weekly_structure": [
                {"day": "每天", "type": "yoga", "focus": "放松", "duration": 15, "time": "睡前1小时"},
                {"day": "每天", "action": "固定作息", "time": "23:00-07:00"},
                {"day": "每天", "action": "远离电子设备", "time": "睡前1小时"}
            ],
            "diet_tips": [
                "下午3点后不喝咖啡/茶",
                "晚餐不宜过饱",
                "睡前可喝温牛奶"
            ]
        },
        "减压放松": {
            "description": "身心放松计划",
            "weekly_structure": [
                {"day": "每天", "action": "5分钟深呼吸", "time": "任意时间"},
                {"day": "每周3次", "type": "yoga", "focus": "放松", "duration": 20},
                {"day": "周末", "type": "outdoor", "duration": 60}
            ],
            "diet_tips": [
                "多吃富含镁的食物（坚果、绿叶蔬菜）",
                "补充B族维生素",
                "避免过量咖啡因"
            ]
        }
    }

    @classmethod
    def get_exercise(cls, exercise_type: str, level: str = "中级", focus: str = None) -> str:
        """获取随机运动建议"""
        if exercise_type in cls.EXERCISES:
            if isinstance(cls.EXERCISES[exercise_type], dict):
                if focus and focus in cls.EXERCISES[exercise_type]:
                    return random.choice(cls.EXERCISES[exercise_type][focus])
                elif level in cls.EXERCISES[exercise_type]:
                    return random.choice(cls.EXERCISES[exercise_type][level])
                else:
                    # 取第一个可用的
                    first_key = list(cls.EXERCISES[exercise_type].keys())[0]
                    return random.choice(cls.EXERCISES[exercise_type][first_key])
        return "快走 30分钟"

    @classmethod
    def get_plan(cls, goal_type: str, customizations: Dict = None) -> Dict:
        """获取个性化计划模板"""
        base_plan = cls.PLAN_TEMPLATES.get(goal_type, cls.PLAN_TEMPLATES["减重"]).copy()

        # 应用自定义设置
        if customizations:
            if customizations.get("preferred_exercises"):
                # 偏好运动优先
                pass
            if customizations.get("time_constraint"):
                # 时间限制调整
                pass

        return base_plan

class PlanGenerator:
    """计划生成引擎"""

    def __init__(self, memory: MemorySystem):
        self.memory = memory
        self.exercise_db = ToolConfig.EXERCISE_DATABASE

    # planner.py - 修改 generate_plan 方法

    def generate_plan(self, user_id: str, goal: HealthGoal, profile: UserProfile, user_message: str = "") -> Dict:
        """根据目标和偏好生成个性化计划"""

        # 根据目标类型选择策略
        if "减重" in goal.type or "减" in goal.target:
            return self._generate_weight_loss_plan(profile, goal, user_message)
        elif "增肌" in goal.type:
            return self._generate_muscle_gain_plan(profile, goal, user_message)
        elif "耐力" in goal.type:
            return self._generate_endurance_plan(profile, goal, user_message)
        elif "睡眠" in goal.type:
            return self._generate_sleep_plan(profile, goal, user_message)
        elif "压力" in goal.type or "放松" in goal.type:
            return self._generate_stress_relief_plan(profile, goal, user_message)
        else:
            # 默认返回保持健康计划
            return self._generate_maintenance_plan(profile, goal, user_message)

    def _generate_maintenance_plan(self, profile: UserProfile, goal: HealthGoal, user_message: str = "") -> Dict:
        """保持健康计划"""
        preferred = profile.exercise_preferences or ["快走", "瑜伽"]

        # 检查用户消息中是否有特定需求
        if "吃" in user_message:
            daily_suggestions = [
                "晚餐在睡前3小时完成",
                "想吃零食时先喝杯水",
                "选择健康替代品：水果代替甜食"
            ]
        elif "睡眠" in user_message:
            daily_suggestions = [
                "固定作息时间",
                "睡前1小时关闭电子设备",
                "睡前做深呼吸放松"
            ]
        else:
            daily_suggestions = [
                "每天走8000步",
                "多吃蔬菜水果",
                "保持充足睡眠"
            ]

        return {
            "weekly_plan": [
                {"day": "周一", "activity": f"{random.choice(preferred)} 30分钟"},
                {"day": "周三", "activity": f"{random.choice(preferred)} 30分钟"},
                {"day": "周五", "activity": f"{random.choice(preferred)} 30分钟"},
                {"day": "周末", "activity": "户外活动 60分钟"}
            ],
            "daily_suggestions": daily_suggestions,
            "tips": ["保持习惯比强度更重要", "循序渐进，不要急于求成"],
            "alternatives": {}
        }

    def _generate_weight_loss_plan(self, profile: UserProfile, goal: HealthGoal, user_message: str) -> Dict:
        """生成减重计划"""
        # 解析具体目标
        import re
        target_weight = None
        weight_match = re.search(r'(\d+)斤', user_message)
        if weight_match:
            target_weight = weight_match.group(1)

        # 根据用户偏好选择运动
        preferred = profile.exercise_preferences
        if not preferred:
            preferred = ["快走", "慢跑", "游泳"]

        # 生成周计划
        weekly_plan = []
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for i, day in enumerate(days):
            if i < 5:  # 工作日
                exercise = preferred[i % len(preferred)]
                weekly_plan.append({
                    "day": day,
                    "activity": f"{exercise} 30分钟",
                    "intensity": "中等"
                })
            else:  # 周末
                weekly_plan.append({
                    "day": day,
                    "activity": f"户外活动 45分钟",
                    "intensity": "轻松"
                })

        # 根据目标生成特定建议
        specific_tips = []
        if target_weight:
            specific_tips.append(f"目标是减到{target_weight}斤，建议每周减重0.5-1斤比较健康")

        diet_tips = [
            "增加蛋白质摄入，每餐保证有优质蛋白",
            "减少精制碳水，用全谷物替代",
            "每天喝够2L水，饭前喝一杯增加饱腹感",
            "晚餐在睡前3小时完成"
        ]

        return {
            "weekly_plan": weekly_plan[:5],  # 只显示工作日
            "daily_suggestions": specific_tips + diet_tips[:3],
            "tips": ["循序渐进，不要急于求成", "记录饮食和运动，提高觉察"],
            "alternatives": {
                "没时间运动": "爬楼梯代替电梯，走路通勤",
                "下雨天": "室内拉伸或瑜伽 20分钟"
            }
        }

    def _generate_muscle_gain_plan(self, profile: UserProfile, goal: HealthGoal, user_message: str) -> Dict:
        """生成增肌计划"""
        return {
            "weekly_plan": [
                {"day": "周一", "focus": "上肢", "exercises": ["俯卧撑", "哑铃弯举"], "sets": 3, "reps": 10},
                {"day": "周三", "focus": "下肢", "exercises": ["深蹲", "弓步蹲"], "sets": 3, "reps": 12},
                {"day": "周五", "focus": "核心", "exercises": ["平板支撑", "卷腹"], "sets": 3, "reps": "60秒/15次"}
            ],
            "daily_suggestions": [
                "运动后30分钟内补充蛋白质",
                "保证每餐有优质蛋白（鸡胸、鱼、蛋、豆制品）",
                "睡眠至少7小时促进肌肉恢复"
            ],
            "tips": ["渐进式超负荷：每周增加一点重量或次数"]
        }

    def _generate_sleep_plan(self, profile: UserProfile, goal: HealthGoal, user_message: str) -> Dict:
        """生成改善睡眠计划"""
        return {
            "weekly_plan": [
                {"day": "每天", "action": "固定时间上床和起床", "time": "23:00-07:00"},
                {"day": "睡前1小时", "action": "关闭电子设备", "benefit": "减少蓝光干扰"},
                {"day": "睡前30分钟", "action": "放松练习（深呼吸/轻拉伸）", "benefit": "放松身心"}
            ],
            "daily_suggestions": [
                "下午3点后不喝咖啡/浓茶",
                "睡前泡脚15分钟",
                "保持卧室黑暗安静"
            ],
            "tips": ["如果躺下20分钟睡不着，起来做点放松的事"]
        }

    def _generate_stress_relief_plan(self, profile: UserProfile, goal: HealthGoal, user_message: str) -> Dict:
        """生成减压放松计划"""
        return {
            "weekly_plan": [
                {"day": "每天", "action": "5分钟深呼吸", "time": "任意时间", "effect": "即时放松"},
                {"day": "每周2-3次", "action": "瑜伽或拉伸", "duration": 20},
                {"day": "周末", "action": "户外散步", "duration": 60}
            ],
            "daily_suggestions": [
                "工作间隙站起来活动",
                "正念饮食：专注地吃一餐",
                "写感恩日记"
            ],
            "tips": ["把压力事件写下来，有助于梳理"]
        }

    def _generate_endurance_plan(self, profile: UserProfile, goal: HealthGoal) -> Dict:
        """提升耐力计划"""
        return {
            "weekly_plan": [
                {"day": "周二", "type": "慢跑", "duration": 20, "pace": "舒适"},
                {"day": "周四", "type": "快走+慢跑交替", "duration": 30},
                {"day": "周六", "type": "长距离慢跑", "duration": 45},
                {"day": "周日", "type": "游泳/骑车", "duration": 40}
            ],
            "daily_suggestions": [
                "循序渐进增加距离",
                "保持呼吸节奏",
                "运动前充分热身"
            ],
            "tips": ["耐力提升需要时间，关注时间而非速度"],
            "alternatives": {}
        }

    def adjust_plan(self, user_id: str, feedback: str, current_plan: Dict) -> Dict:
        """
        根据用户反馈调整计划
        """
        profile = self.memory.get_user_profile(user_id)

        # 简单反馈分析
        adjusted = current_plan.copy()

        if "太难" in feedback or "太累" in feedback:
            # 降低强度
            if "weekly_plan" in adjusted:
                for item in adjusted["weekly_plan"]:
                    if "duration" in item:
                        item["duration"] = max(15, item["duration"] - 5)
                    if "intensity" in item:
                        if item["intensity"] == "高强度":
                            item["intensity"] = "中等"
                        elif item["intensity"] == "中等":
                            item["intensity"] = "低"

            adjusted["tips"] = adjusted.get("tips", []) + ["从更轻松的版本开始，循序渐进"]

        elif "太简单" in feedback:
            # 增加挑战
            if "weekly_plan" in adjusted:
                for item in adjusted["weekly_plan"]:
                    if "duration" in item:
                        item["duration"] = min(60, item["duration"] + 5)

        return adjusted