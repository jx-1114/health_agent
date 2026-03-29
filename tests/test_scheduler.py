# test_scheduler.py
"""测试主动提醒功能"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent import HealthAgent
import time

# 初始化 Agent
print("1. 初始化 Agent...")
api_key = "sk-aaf9ea6f4d91454e82a0f25c75e770f4"
agent = HealthAgent(api_key=api_key, model="qwen-max")

# 创建测试用户
user_id = "test_user"

# 手动调用主动询问
print("\n2. 测试主动询问 (active_checkin)...")
result = agent.active_checkin(user_id)
if result:
    print(f"   {result['message']}")
    print(f"   原因: {result['reason']}")
else:
    print("   暂无主动询问需要")

# 测试添加每日提醒
print("\n3. 测试添加每日提醒...")
agent.scheduler.add_daily_checkin(user_id, hour=9, minute=0)
agent.scheduler.add_exercise_reminder(user_id, hour=18, minute=0)

# 手动触发一次提醒（模拟时间到达）
print("\n4. 手动触发提醒（模拟）...")

# 模拟主动询问
def mock_checkin():
    print("\n   📅 模拟主动询问:")
    result = agent.active_checkin(user_id)
    if result:
        print(f"      消息: {result['message']}")

# 模拟运动提醒
def mock_reminder():
    print("\n   🏃 模拟运动提醒:")
    reminder = "🏃 该运动啦！\n\n今天记得抽时间活动一下，哪怕只是散步15分钟也对健康有益。\n运动完记得来记录哦！✨"
    print(f"      消息: {reminder}")

mock_checkin()
mock_reminder()

print("\n✅ 测试完成！调度器正在后台运行...")
print("   如需停止，按 Ctrl+C")