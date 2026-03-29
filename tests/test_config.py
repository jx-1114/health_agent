# test_config.py
"""
简单测试配置加载
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 手动加载
env_file = Path(__file__).parent / ".env"
print(f"查找配置文件: {env_file}")
print(f"文件存在: {env_file.exists()}")

if env_file.exists():
    load_dotenv(env_file)
    print("✅ 已加载 .env 文件")

    # 直接读取环境变量
    print("\n环境变量值:")
    print(f"  QWEATHER_API_KEY: {os.getenv('QWEATHER_API_KEY', '未设置')}")
    print(f"  EDAMAM_APP_ID: {os.getenv('EDAMAM_APP_ID', '未设置')}")
    print(
        f"  EDAMAM_APP_KEY: {os.getenv('EDAMAM_APP_KEY', '未设置')[:10] if os.getenv('EDAMAM_APP_KEY') else '未设置'}...")

    # 导入 config 测试
    print("\n" + "=" * 50)
    print("导入 config 模块测试:")
    from config import APIConfig

    APIConfig.print_status()

else:
    print("❌ .env 文件不存在")