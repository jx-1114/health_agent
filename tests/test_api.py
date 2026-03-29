# test_api_correct.py
"""使用 Python 正确测试 API"""

import requests
import json

url = "http://127.0.0.1:8000"

# 1. 初始化
print("1. 初始化 Agent...")
init_response = requests.post(
    f"{url}/init",
    json={
        "user_id": "me",
        "api_key": "sk-aaf9ea6f4d91454e82a0f25c75e770f4",
        "model": "qwen-max"
    }
)
print(f"   状态码: {init_response.status_code}")
print(f"   响应: {init_response.json()}")

# 2. 发送中文消息
print("\n2. 发送天气查询...")
chat_response = requests.post(
    f"{url}/chat",
    json={
        "user_id": "me",
        "message": "武汉今天天气怎么样？"
    }
)

print(f"   状态码: {chat_response.status_code}")
data = chat_response.json()
print(f"\n   返回消息:")
print(f"   {data.get('message', '')}")
print(f"\n   action_type: {data.get('action_type')}")