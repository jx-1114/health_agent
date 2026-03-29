# test_config_loading.py
"""
测试配置加载
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 50)
print("配置加载测试")
print("=" * 50)

# 查找 .env 文件
env_file = Path(__file__).parent / ".env"
print(f"查找配置文件: {env_file}")
print(f"文件存在: {env_file.exists()}")

if env_file.exists():
    # 读取文件内容
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"\n文件内容:\n{content}")

    # 加载环境变量
    load_dotenv(env_file)

    print("\n加载后的环境变量:")
    print(f"  QWEATHER_API_KEY: {os.getenv('QWEATHER_API_KEY', '未设置')}")
    print(f"  EDAMAM_APP_ID: {os.getenv('EDAMAM_APP_ID', '未设置')}")
    print(
        f"  EDAMAM_APP_KEY: {os.getenv('EDAMAM_APP_KEY', '未设置')[:10] if os.getenv('EDAMAM_APP_KEY') else '未设置'}...")

    # 导入 config 测试
    print("\n" + "=" * 50)
    print("导入 config 模块:")
    from config import APIConfig

    APIConfig.print_status()
else:
    print("❌ .env 文件不存在，请创建")