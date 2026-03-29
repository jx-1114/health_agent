# test_agent_debug.py
"""带调试信息的 Agent 测试"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("开始调试测试")
print("=" * 60)

# 1. 导入模块
print("\n[1] 导入模块...")
try:
    from agent import HealthAgent
    print("✅ agent 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 初始化 Agent
print("\n[2] 初始化 Agent...")
try:
    api_key = "sk-aaf9ea6f4d91454e82a0f25c75e770f4"
    agent = HealthAgent(api_key=api_key, model="qwen-max")
    print("✅ Agent 初始化成功")
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试 extract_city 函数
print("\n[3] 测试城市提取函数...")
from agent import extract_city, CHINA_CITIES
print(f"城市列表包含武汉: {'武汉' in CHINA_CITIES}")
city = extract_city("武汉今天天气怎么样？")
print(f"提取的城市: {city}")

# 4. 测试天气查询
print("\n[4] 测试 WeatherChecker...")
from tools import WeatherChecker
try:
    print("  调用 get_weather('武汉')...")
    weather = WeatherChecker.get_weather("武汉")
    print(f"  返回结果: {weather}")
    print(f"  城市: {weather.get('city')}")
    print(f"  天气: {weather.get('condition')}")
    print(f"  温度: {weather.get('temperature')}°C")
    print("✅ WeatherChecker 工作正常")
except Exception as e:
    print(f"❌ WeatherChecker 失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 测试 Agent 处理（带超时）
print("\n[5] 测试 Agent.process_input...")
print("  发送: '武汉今天天气怎么样？'")

import threading
import time

result = None
error = None

def run_agent():
    global result, error
    try:
        result = agent.process_input(
            user_id="test_user",
            user_input="武汉今天天气怎么样？",
            session_id=None
        )
    except Exception as e:
        error = e

# 设置超时
thread = threading.Thread(target=run_agent)
thread.start()
thread.join(timeout=15)  # 15秒超时

if thread.is_alive():
    print("❌ Agent 处理超时（超过15秒）！")
    print("  可能卡在某个地方，请检查：")
    print("  1. 天气 API 是否卡住？")
    print("  2. 内存操作是否死锁？")
    print("  3. 是否有无限循环？")
elif error:
    print(f"❌ Agent 处理出错: {error}")
    import traceback
    traceback.print_exc()
else:
    print("\n✅ Agent 处理成功！")
    print("=" * 60)
    print("响应消息:")
    print("=" * 60)
    print(result.get('message', '')[:500])
    print("\n建议:", result.get('suggestions', []))

print("\n调试测试完成")