# test_nutrition.py
"""测试本地营养数据库"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools import NutritionAnalyzer


def test_nutrition():
    print("=" * 60)
    print("测试本地营养数据库")
    print("=" * 60)

    test_meals = [
        "一个苹果",
        "150克鸡胸肉",
        "一碗米饭",
        "一杯牛奶",
        "一个鸡蛋和一片全麦面包",
        "西兰花炒鸡胸肉",
        "不知道的食物名称"
    ]

    for meal in test_meals:
        print(f"\n{'=' * 40}")
        print(f"📝 分析: {meal}")
        print('=' * 40)

        result = NutritionAnalyzer.analyze_meal(meal)

        print(f"  热量: {result['estimated_calories']} kcal")
        print(f"  蛋白质: {result['nutrition']['protein']} g")
        print(f"  碳水: {result['nutrition']['carbs']} g")
        print(f"  脂肪: {result['nutrition']['fat']} g")
        print(f"  膳食纤维: {result['nutrition']['fiber']} g")

        if result['found_items']:
            print(f"  ✅ 识别到: {', '.join(result['found_items'])}")
        else:
            print(f"  ⚠️ 未识别到食物")

        if result['suggestions']:
            print(f"  💡 建议: {result['suggestions'][0]}")


if __name__ == "__main__":
    test_nutrition()