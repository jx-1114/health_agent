# test_new_features.py
"""
测试新功能
"""
import requests
import json
from tools import WeatherChecker, NutritionAnalyzer
from planner import ExerciseDatabase


def test_weather():
    """测试天气查询"""
    print("\n" + "=" * 50)
    print("1. 测试天气查询")
    print("=" * 50)

    weather = WeatherChecker.get_weather("北京", use_api=True)
    print(f"城市: {weather['city']}")
    print(f"天气: {weather['condition']}")
    print(f"温度: {weather['temperature']}°C")
    print(f"湿度: {weather['humidity']}%")
    print(f"适合户外: {'是' if weather['suitable_for_outdoor'] else '否'}")
    print(f"数据来源: {weather['source']}")


def test_nutrition():
    """测试饮食分析"""
    print("\n" + "=" * 50)
    print("2. 测试饮食分析")
    print("=" * 50)

    meal = "一个苹果和一杯牛奶"
    analysis = NutritionAnalyzer.analyze_meal(meal, use_api=True)
    print(f"食物: {analysis['food']}")
    print(f"热量: {analysis.get('estimated_calories', analysis.get('calories', 0))} 千卡")
    print(f"营养: {analysis.get('nutrition', {})}")
    print(f"数据来源: {analysis.get('source', '本地')}")
    if analysis.get('suggestions'):
        print(f"建议: {analysis['suggestions']}")


def test_exercise_db():
    """测试运动数据库"""
    print("\n" + "=" * 50)
    print("3. 测试运动数据库")
    print("=" * 50)

    # 测试获取运动
    exercise = ExerciseDatabase.get_exercise("cardio", "中级")
    print(f"推荐运动: {exercise}")

    # 测试获取计划
    plan = ExerciseDatabase.get_plan("减重")
    print(f"计划名称: {plan['description']}")
    print(f"周计划结构: {plan['weekly_structure'][:3]}")


def test_agent_with_weather():
    """测试 Agent 结合天气"""
    print("\n" + "=" * 50)
    print("4. 测试 Agent 结合天气")
    print("=" * 50)

    # 获取天气
    weather = WeatherChecker.get_weather("北京")

    # 根据天气生成建议
    if weather['suitable_for_outdoor']:
        suggestion = f"今天{weather['condition']}，温度{weather['temperature']}°C，很适合户外运动！建议去公园散步或慢跑。"
    else:
        suggestion = f"今天{weather['condition']}，不太适合户外运动。建议在家做瑜伽或拉伸。"

    print(suggestion)


def main():
    print("🚀 开始测试新功能")

    # 显示配置状态
    from config import APIConfig
    print(f"\n配置状态:")
    print(f"  天气 API: {'✅ 已配置' if APIConfig.is_weather_configured() else '❌ 未配置'}")
    print(f"  饮食 API: {'✅ 已配置' if APIConfig.is_nutrition_configured() else '❌ 未配置'}")

    # 运行测试
    test_weather()
    test_nutrition()
    test_exercise_db()
    test_agent_with_weather()

    print("\n✅ 测试完成！")


if __name__ == "__main__":
    main()