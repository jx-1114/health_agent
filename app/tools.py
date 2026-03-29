# tools.py
"""
工具层 - Agent 可调用的外部能力
"""
import re

import requests
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .config import APIConfig
from dotenv import load_dotenv

load_dotenv()

QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY")
QWEATHER_HOST = os.getenv("QWEATHER_HOST", "ne6fr8btct.re.qweatherapi.com")


class ExercisePlanner:
    """运动计划工具"""

    @staticmethod
    def suggest_exercise(goal: str, available_time: int, equipment: List[str] = None) -> Dict:
        """
        根据目标和可用时间推荐运动
        """
        equipment = equipment or []

        # 无器材选项
        no_equipment = {
            "减重": ["开合跳", "高抬腿", "波比跳", "登山跑"],
            "增肌": ["俯卧撑", "深蹲", "弓步蹲", "平板支撑"],
            "放松": ["深呼吸", "颈部拉伸", "肩部绕环", "猫牛式"]
        }

        # 有器材选项
        with_equipment = {
            "哑铃": ["哑铃弯举", "哑铃推举", "哑铃划船"],
            "瑜伽垫": ["平板支撑", "瑜伽拉伸", "卷腹"]
        }

        suggestions = []

        # 根据目标推荐
        for key in no_equipment:
            if key in goal:
                exercises = no_equipment[key]
                suggestions.append({
                    "name": exercises[0],
                    "duration": min(available_time, 20),
                    "intensity": "中等",
                    "equipment_needed": "无"
                })
                break

        return {
            "suggestions": suggestions[:3],
            "tips": ["运动前热身5分钟", "运动后拉伸"]
        }


class NutritionAnalyzer:
    """饮食分析工具 - 基于本地数据库（稳定、快速、无限制）"""

    # 完整的本地营养数据库（每100克/每100毫升）
    FOOD_DATABASE = {
        # === 水果 ===
        "苹果": {"calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14, "fiber": 2.4},
        "香蕉": {"calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 23, "fiber": 2.6},
        "橙子": {"calories": 47, "protein": 0.9, "fat": 0.1, "carbs": 12, "fiber": 2.4},
        "草莓": {"calories": 32, "protein": 0.7, "fat": 0.3, "carbs": 8, "fiber": 2.0},
        "蓝莓": {"calories": 57, "protein": 0.7, "fat": 0.3, "carbs": 14, "fiber": 2.4},
        "西瓜": {"calories": 30, "protein": 0.6, "fat": 0.2, "carbs": 8, "fiber": 0.4},

        # === 蛋白质 ===
        "鸡胸肉": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0, "fiber": 0},
        "鸡腿肉": {"calories": 209, "protein": 26, "fat": 10.9, "carbs": 0, "fiber": 0},
        "牛肉": {"calories": 250, "protein": 26, "fat": 15, "carbs": 0, "fiber": 0},
        "猪肉": {"calories": 242, "protein": 27, "fat": 14, "carbs": 0, "fiber": 0},
        "三文鱼": {"calories": 208, "protein": 20, "fat": 13, "carbs": 0, "fiber": 0},
        "鳕鱼": {"calories": 82, "protein": 18, "fat": 0.7, "carbs": 0, "fiber": 0},
        "鸡蛋": {"calories": 155, "protein": 13, "fat": 11, "carbs": 1, "fiber": 0},
        "豆腐": {"calories": 76, "protein": 8, "fat": 4.8, "carbs": 1.9, "fiber": 0.3},
        "豆浆": {"calories": 54, "protein": 3.3, "fat": 1.8, "carbs": 6, "fiber": 0.5},

        # === 主食 ===
        "米饭": {"calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28, "fiber": 0.4},
        "面条": {"calories": 138, "protein": 4.5, "fat": 0.5, "carbs": 30, "fiber": 1.2},
        "全麦面包": {"calories": 265, "protein": 13, "fat": 4, "carbs": 43, "fiber": 7},
        "白面包": {"calories": 265, "protein": 9, "fat": 3.2, "carbs": 49, "fiber": 2.7},
        "燕麦": {"calories": 389, "protein": 16.9, "fat": 6.9, "carbs": 66, "fiber": 10.6},
        "红薯": {"calories": 86, "protein": 1.6, "fat": 0.1, "carbs": 20, "fiber": 3},
        "土豆": {"calories": 77, "protein": 2, "fat": 0.1, "carbs": 17, "fiber": 2.2},

        # === 蔬菜 ===
        "西兰花": {"calories": 34, "protein": 2.8, "fat": 0.4, "carbs": 7, "fiber": 2.6},
        "番茄": {"calories": 18, "protein": 0.9, "fat": 0.2, "carbs": 3.9, "fiber": 1.2},
        "菠菜": {"calories": 23, "protein": 2.9, "fat": 0.4, "carbs": 3.6, "fiber": 2.2},
        "生菜": {"calories": 15, "protein": 1.4, "fat": 0.2, "carbs": 2.9, "fiber": 1.3},
        "胡萝卜": {"calories": 41, "protein": 0.9, "fat": 0.2, "carbs": 10, "fiber": 2.8},
        "黄瓜": {"calories": 15, "protein": 0.7, "fat": 0.1, "carbs": 3.6, "fiber": 0.5},

        # === 奶制品 ===
        "牛奶": {"calories": 42, "protein": 3.4, "fat": 1, "carbs": 5, "fiber": 0},
        "酸奶": {"calories": 61, "protein": 3.5, "fat": 0.4, "carbs": 12, "fiber": 0},
        "奶酪": {"calories": 402, "protein": 25, "fat": 33, "carbs": 1.3, "fiber": 0},

        # === 坚果 ===
        "杏仁": {"calories": 579, "protein": 21, "fat": 49, "carbs": 22, "fiber": 12},
        "核桃": {"calories": 654, "protein": 15, "fat": 65, "carbs": 14, "fiber": 7},
        "腰果": {"calories": 553, "protein": 18, "fat": 44, "carbs": 30, "fiber": 3.3},

        # === 油脂 ===
        "橄榄油": {"calories": 884, "protein": 0, "fat": 100, "carbs": 0, "fiber": 0},
        "花生油": {"calories": 884, "protein": 0, "fat": 100, "carbs": 0, "fiber": 0},
    }

    @classmethod
    def analyze_meal(cls, meal_description: str, use_api: bool = False) -> Dict:
        """
        分析饮食记录

        Args:
            meal_description: 食物描述，如"一个苹果"或"150克鸡胸肉"
            use_api: 是否使用 API（已废弃，保留参数兼容性）

        Returns:
            营养分析结果
        """
        return cls._local_analysis(meal_description)

    @classmethod
    def _local_analysis(cls, meal_description: str) -> Dict:
        """本地分析（基于数据库）"""

        total = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0, "fiber": 0}
        found_items = []

        # 解析食物
        for food, values in cls.FOOD_DATABASE.items():
            if food in meal_description:
                # 提取数量（克数）
                quantity = 1
                match = re.search(r'(\d+)\s*克', meal_description)
                if match:
                    quantity = int(match.group(1)) / 100

                # 提取数量（个）
                count_match = re.search(r'(\d+)\s*个', meal_description)
                if count_match and food in ["鸡蛋", "苹果", "香蕉", "橙子"]:
                    # 假设每个约100克
                    quantity = int(count_match.group(1)) * 1.0

                for key in total:
                    total[key] += values[key] * quantity
                found_items.append(food)

        # 生成建议
        suggestions = []
        if total["protein"] < 20:
            suggestions.append("蛋白质摄入不足，建议增加豆制品或瘦肉")
        if total["fiber"] < 10 and total["carbs"] > 0:
            suggestions.append("膳食纤维不足，建议多吃蔬菜水果")
        if total["calories"] > 800:
            suggestions.append("这一餐热量较高，建议增加运动消耗")
        if total["fat"] > 30:
            suggestions.append("脂肪摄入较多，建议选择更清淡的烹饪方式")

        # 如果没有识别到任何食物
        if not found_items:
            suggestions.append("我暂时不认识这种食物，你可以试试用中文描述，如'一个苹果'或'150克鸡胸肉'")

        return {
            "food": meal_description[:50],
            "estimated_calories": round(total["calories"], 1),
            "nutrition": {
                "protein": round(total["protein"], 1),
                "fat": round(total["fat"], 1),
                "carbs": round(total["carbs"], 1),
                "fiber": round(total["fiber"], 1)
            },
            "found_items": found_items,
            "suggestions": suggestions,
            "source": "本地营养数据库"
        }

class NotificationSender:
    """通知推送工具"""

    # 邮件配置
    EMAIL_CONFIG = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": APIConfig.EMAIL_SENDER,
        "sender_password": APIConfig.EMAIL_PASSWORD
    }

    # 微信配置
    WECHAT_WEBHOOK = APIConfig.WECHAT_WEBHOOK

    @classmethod
    def set_email_config(cls, email: str, password: str, smtp_server: str = "smtp.gmail.com"):
        """设置邮件配置"""
        cls.EMAIL_CONFIG["sender_email"] = email
        cls.EMAIL_CONFIG["sender_password"] = password
        cls.EMAIL_CONFIG["smtp_server"] = smtp_server

    @classmethod
    def set_wechat_webhook(cls, webhook_url: str):
        """设置微信 webhook"""
        cls.WECHAT_WEBHOOK = webhook_url

    @staticmethod
    def send_email(to_email: str, subject: str, content: str) -> Dict:
        """发送邮件通知"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            if not NotificationSender.EMAIL_CONFIG["sender_email"]:
                return {"status": "error", "message": "未配置发件邮箱"}

            msg = MIMEMultipart()
            msg['From'] = NotificationSender.EMAIL_CONFIG["sender_email"]
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(content, 'plain', 'utf-8'))

            server = smtplib.SMTP(
                NotificationSender.EMAIL_CONFIG["smtp_server"],
                NotificationSender.EMAIL_CONFIG["smtp_port"]
            )
            server.starttls()
            server.login(
                NotificationSender.EMAIL_CONFIG["sender_email"],
                NotificationSender.EMAIL_CONFIG["sender_password"]
            )
            server.send_message(msg)
            server.quit()

            return {"status": "success", "message": "邮件已发送"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_wechat(content: str) -> Dict:
        """发送微信通知"""
        if not NotificationSender.WECHAT_WEBHOOK:
            return {"status": "error", "message": "未配置微信 webhook"}

        try:
            response = requests.post(
                NotificationSender.WECHAT_WEBHOOK,
                json={
                    "msgtype": "text",
                    "text": {"content": content}
                },
                timeout=10
            )
            if response.status_code == 200:
                return {"status": "success", "message": "微信通知已发送"}
            return {"status": "error", "message": f"发送失败: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_push_deer(title: str, content: str, push_key: str = None) -> Dict:
        """使用 PushDeer 推送"""
        key = push_key or APIConfig.PUSHDEER_KEY
        if not key:
            return {"status": "error", "message": "未配置 PushDeer 密钥"}

        try:
            response = requests.post(
                "https://api2.pushdeer.com/message/push",
                params={
                    "pushkey": key,
                    "text": title,
                    "desp": content,
                    "type": "markdown"
                },
                timeout=10
            )
            return {"status": "success", "message": "推送已发送"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class ProgressTracker:
    """进度追踪工具"""

    @staticmethod
    def update_progress(user_id: str, goal_type: str, value: float) -> Dict:
        """
        更新用户进度
        """
        return {
            "status": "updated",
            "message": f"进度已更新",
            "value": value
        }

    @staticmethod
    def get_summary(user_id: str, period: str = "week") -> Dict:
        """
        获取进度摘要
        """
        # 模拟数据
        return {
            "period": period,
            "total_exercises": 4,
            "total_minutes": 120,
            "goals_completed": 1,
            "consistency": "75%"
        }


class ReminderScheduler:
    """提醒调度工具"""

    def __init__(self):
        self.reminders = []

    def schedule(self, user_id: str, content: str, time: str) -> Dict:
        """
        设置提醒
        """
        reminder = {
            "id": len(self.reminders) + 1,
            "user_id": user_id,
            "content": content,
            "time": time,
            "created_at": datetime.now().isoformat()
        }
        self.reminders.append(reminder)

        return {
            "status": "scheduled",
            "reminder": reminder
        }


# tools.py - 修复天气查询

class WeatherChecker:
    """天气查询工具 - 支持和风天气 API v7"""

    QWEATHER_API_KEY = APIConfig.QWEATHER_API_KEY
    API_HOST = "ne6fr8btct.re.qweatherapi.com"  # 从你的控制台获取

    # 城市映射表
    CITY_MAP = {
        "北京": "101010100",
        "上海": "101020100",
        "广州": "101280101",
        "深圳": "101280601",
        "杭州": "101210101",
        "成都": "101270101",
        "武汉": "101200101",
        "南京": "101190101",
        "西安": "101110101",
        "重庆": "101040100",
        "天津": "101030100",
        "苏州": "101190401",
        "长沙": "101250101",
        "郑州": "101180101",
        "青岛": "101120201"
    }

    @classmethod
    def set_api_key(cls, api_key: str):
        """设置 API 密钥"""
        cls.QWEATHER_API_KEY = api_key

    @classmethod
    def get_weather(cls, city_name: str = "北京") -> Dict:
        """
        获取天气信息 - 使用正确的认证方式

        Args:
            city_name: 城市名称

        Returns:
            天气信息字典
        """
        # 获取城市 ID
        city_id = cls.CITY_MAP.get(city_name)
        if not city_id:
            return cls._get_mock_weather(city_name, error=f"不支持的城市: {city_name}")

        if cls.QWEATHER_API_KEY and cls.API_HOST:
            try:
                # 正确的请求方式：使用 API Host 和 X-QW-Api-Key 请求头
                url = f"https://{cls.API_HOST}/v7/weather/now"
                params = {
                    "location": city_id
                }
                headers = {
                    "X-QW-Api-Key": cls.QWEATHER_API_KEY
                }

                print(f"[DEBUG] 请求 URL: {url}")
                print(f"[DEBUG] 参数: {params}")
                print(f"[DEBUG] 请求头: X-QW-Api-Key={cls.QWEATHER_API_KEY[:8]}...")

                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=10
                )

                print(f"[DEBUG] 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"[DEBUG] API 返回码: {data.get('code')}")

                    if data.get("code") == "200":
                        now = data.get("now", {})
                        return {
                            "city": city_name,
                            "condition": now.get("text", "未知"),
                            "temperature": now.get("temp", "N/A"),
                            "humidity": now.get("humidity", "N/A"),
                            "wind_speed": now.get("windSpeed", "N/A"),
                            "wind_dir": now.get("windDir", "未知"),
                            "feels_like": now.get("feelsLike", "N/A"),
                            "suitable_for_outdoor": cls._is_suitable(
                                now.get("text", ""),
                                float(now.get("temp", 25))
                            ),
                            "source": "和风天气",
                            "update_time": now.get("obsTime", "")
                        }
                    else:
                        print(f"[ERROR] API 返回错误码: {data.get('code')}, 消息: {data}")
                        return cls._get_mock_weather(city_name, error=f"API错误: {data.get('code')}")
                else:
                    print(f"[ERROR] HTTP 错误: {response.status_code}")
                    if response.status_code == 403:
                        print("[ERROR] 可能原因: API Key 无效或 IP 未在白名单中")
                        print("   解决步骤:")
                        print("   1. 登录 https://console.qweather.com/")
                        print("   2. 检查 API Key 是否正确")
                        print("   3. 添加 IP 白名单: 127.0.0.1")

            except requests.exceptions.RequestException as e:
                print(f"[ERROR] 天气 API 调用异常: {e}")
            except Exception as e:
                print(f"[ERROR] 未知错误: {e}")
                import traceback
                traceback.print_exc()

        # 降级：返回模拟数据
        print("[INFO] 使用模拟天气数据")
        return cls._get_mock_weather(city_name)

    @classmethod
    def _get_mock_weather(cls, city_name: str, error: str = None) -> Dict:
        """返回模拟天气数据"""
        result = {
            "city": city_name,
            "condition": "晴天",
            "temperature": 22,
            "humidity": 45,
            "wind_speed": 2,
            "wind_dir": "东北风",
            "feels_like": 22,
            "suitable_for_outdoor": True,
            "source": "模拟数据"
        }
        if error:
            result["error"] = error
        return result

    @staticmethod
    def _is_suitable(condition: str, temp: float) -> bool:
        """判断是否适合户外运动"""
        unsuitable = ["暴雨", "雷阵雨", "大雨", "大雪", "暴雪", "台风", "沙尘暴", "大雾", "霾"]
        for uc in unsuitable:
            if uc in condition:
                return False
        if temp < 0 or temp > 35:
            return False
        return True


class Motivator:
    """激励消息生成工具"""

    @staticmethod
    def generate_message(user_name: str, achievement: str, progress: int) -> str:
        """
        生成个性化激励消息
        """
        messages = [
            f"太棒了，{user_name}！你已经完成{progress}%的目标，继续加油！",
            f"每一次坚持都在为更好的自己铺路，{user_name}！",
            f"你已经取得了很大的进步，相信你一定可以的！"
        ]
        return messages[progress // 34 % 3]  # 简单的轮换