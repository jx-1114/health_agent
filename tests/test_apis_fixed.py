# test_apis_fixed.py
"""测试营养分析 API"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools import NutritionAnalyzer
from config import APIConfig


def test_nutrition():
    print("=" * 60)
    print("测试营养分析 API")
    print("=" * 60)

    print(f"\n配置信息:")
    print(f"  App ID: {APIConfig.EDAMAM_APP_ID}")
    print(f"  App Key: {APIConfig.EDAMAM_APP_KEY[:8]}...")

    # 测试多种食物
    meals = [
        "一个苹果",
        "鸡胸肉150克",
        "米饭200克",
        "一杯牛奶",
        "一个鸡蛋和一片全麦面包"
    ]

    for meal in meals:
        print(f"\n{'=' * 40}")
        print(f"分析: {meal}")
        print('=' * 40)

        analysis = NutritionAnalyzer.analyze_meal(meal, use_api=True)

        print(f"  热量: {analysis.get('calories', analysis.get('estimated_calories', 0))} kcal")
        print(f"  蛋白质: {analysis.get('nutrition', {}).get('protein', 0)} g")
        print(f"  碳水: {analysis.get('nutrition', {}).get('carbs', 0)} g")
        print(f"  脂肪: {analysis.get('nutrition', {}).get('fat', 0)} g")
        if 'fiber' in analysis.get('nutrition', {}):
            print(f"  膳食纤维: {analysis['nutrition']['fiber']} g")
        print(f"  数据来源: {analysis.get('source', '未知')}")

        if analysis.get('source') == "Edamam":
            print(f"  ✅ 成功使用真实 API 数据！")
            if 'weight' in analysis:
                print(f"  食物重量: {analysis['weight']} g")
        else:
            print(f"  ⚠️ 使用本地分析（降级方案）")
            if analysis.get('suggestions'):
                print(f"  建议: {analysis['suggestions'][:2]}")


def test_specific_meal():
    """测试一个具体餐食的详细营养"""
    print("\n" + "=" * 60)
    print("详细营养分析示例")
    print("=" * 60)

    meal = "一份鸡胸肉沙拉，包含150克鸡胸肉、生菜、番茄和橄榄油"
    print(f"\n分析: {meal}")

    analysis = NutritionAnalyzer.analyze_meal(meal, use_api=True)

    print(f"\n📊 营养数据:")
    print(f"  热量: {analysis.get('calories', analysis.get('estimated_calories', 0))} kcal")

    nutrition = analysis.get('nutrition', {})
    print(f"  蛋白质: {nutrition.get('protein', 0)} g")
    print(f"  碳水: {nutrition.get('carbs', 0)} g")
    print(f"  脂肪: {nutrition.get('fat', 0)} g")

    if 'fiber' in nutrition:
        print(f"  膳食纤维: {nutrition['fiber']} g")

    print(f"\n📌 数据来源: {analysis.get('source', '未知')}")


if __name__ == "__main__":
    test_nutrition()
    test_specific_meal()
    print("\n✅ 测试完成")