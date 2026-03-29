# config.py
"""
健康与健身 Agent 配置文件
"""
# app/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# 确保数据目录存在
DATA_DIR.mkdir(exist_ok=True)

# 加载环境变量
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)

class ModelConfig:
    """模型配置"""
    DEFAULT_MODEL = "qwen-max"  # 或 deepseek-chat
    API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DEFAULT_API_KEY = os.getenv("LLM_API_KEY", "")

    TEMPERATURE = 0.7
    MAX_TOKENS = 1000


class AgentConfig:
    """Agent 核心配置"""
    # 记忆配置
    SHORT_TERM_EXPIRY = 3600  # 短期记忆过期时间（秒）
    WORKING_MEMORY_DAYS = 7  # 工作记忆保留天数

    # 主动干预配置
    CHECKIN_HOURS = [9, 14, 20]  # 主动询问时间点
    REMINDER_HOURS = [8, 12, 18]  # 提醒时间点

    # 目标类型
    GOAL_TYPES = ["减重", "增肌", "提升耐力", "改善睡眠", "减压放松", "保持健康"]

    # 运动类型
    EXERCISE_TYPES = ["有氧运动", "力量训练", "瑜伽/拉伸", "高强度间歇", "户外活动"]

    # 饮食偏好
    DIET_TYPES = ["常规饮食", "低碳饮食", "高蛋白饮食", "素食", "地中海饮食"]


class ToolConfig:
    """工具配置"""
    # WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
    # NUTRITION_API_KEY = os.getenv("NUTRITION_API_KEY", "")

    # 运动库
    EXERCISE_DATABASE = {
        "有氧运动": ["快走", "慢跑", "游泳", "骑车", "跳绳", "椭圆机"],
        "力量训练": ["深蹲", "俯卧撑", "引体向上", "哑铃弯举", "平板支撑", "弓步蹲"],
        "瑜伽/拉伸": ["猫牛式", "下犬式", "婴儿式", "坐姿前屈", "蝴蝶式", "脊柱扭转"],
        "高强度间歇": ["波比跳", "高抬腿", "开合跳", "登山跑", "深蹲跳"],
        "户外活动": ["徒步", "爬山", "划船", "滑雪"]
    }


class APIConfig:
    """第三方 API 配置"""

    # 从环境变量读取
    QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY", "")
    QWEATHER_API_HOST = os.getenv("QWEATHER_API_HOST", "ne6fr8btct.re.qweatherapi.com")  # 新增
    EDAMAM_APP_ID = os.getenv("EDAMAM_APP_ID", "")
    EDAMAM_APP_KEY = os.getenv("EDAMAM_APP_KEY", "")
    PUSHDEER_KEY = os.getenv("PUSHDEER_KEY", "")
    EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK", "")

    @classmethod
    def is_weather_configured(cls):
        return bool(cls.QWEATHER_API_KEY and cls.QWEATHER_API_HOST)

    @classmethod
    def is_nutrition_configured(cls):
        return bool(cls.EDAMAM_APP_ID and cls.EDAMAM_APP_KEY)

    @classmethod
    def print_status(cls):
        """打印配置状态"""
        print("\n📋 API 配置状态:")
        print(f"  🌤️ 天气 API: {'✅ 已配置' if cls.is_weather_configured() else '❌ 未配置'}")
        print(f"  🍎 饮食 API: {'✅ 已配置' if cls.is_nutrition_configured() else '❌ 未配置'}")
        print(f"  🔔 推送通知: {'✅ 已配置' if cls.PUSHDEER_KEY else '❌ 未配置'}")

        if cls.is_weather_configured():
            print(f"     密钥: {cls.QWEATHER_API_KEY[:8]}...")
        if cls.is_nutrition_configured():
            print(f"     App ID: {cls.EDAMAM_APP_ID[:8]}...")

