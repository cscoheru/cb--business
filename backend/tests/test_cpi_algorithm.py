# tests/test_cpi_algorithm.py
"""C-P-I 商机算法系统测试

验证C-P-I算法的三个维度计算正确性:
- Competition (竞争度): Top10_Brand_Share × 0.7 + CPC_Bid_Estimate × 0.3
- Potential (增长潜力): Keyword_Growth × 0.6 + Review_Velocity × 0.4
- Intelligence Gap (信息差): Negative_Review_Sentiment / Product_Feature_Consistency
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import AsyncSessionLocal
from models.card import Card
from services.opportunity_algorithm import opportunity_scorer
from sqlalchemy import select


async def test_cpi_algorithm():
    """测试C-P-I算法在真实Card数据上的表现"""
    print("=" * 80)
    print("C-P-I 商机算法系统测试")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        # 查询一张有Amazon数据的Card
        result = await db.execute(
            select(Card)
            .where(Card.amazon_data.isnot(None))
            .where(Card.category == 'wireless_earbuds')
            .limit(1)
        )
        card = result.scalar_one_or_none()

        if not card:
            print("❌ 没有找到测试用的Card数据")
            return

        print(f"\n📊 测试Card: {card.content.get('summary', {}).get('title', card.category)}")
        print(f"   品类: {card.category}")
        print(f"   产品数量: {len(card.amazon_data.get('products', []))}")

        # 计算C-P-I分数
        print("\n🔬 开始计算C-P-I分数...")
        score_result = await opportunity_scorer.calculate_opportunity_score(card, db)

        # 显示结果
        print("\n" + "=" * 80)
        print("C-P-I 算法评分结果")
        print("=" * 80)

        print(f"\n📈 综合分数: {score_result['total_score']} / 100")
        print(f"   商机类型: {score_result['opportunity_type']}")

        print("\n🎯 三维度详细评分:")
        print(f"   ├─ 竞争度 (C): {score_result['competition']['score']} 分 (权重40%)")
        print(f"   │  └─ 详情: {score_result['competition']['details']}")
        print(f"   ├─ 增长潜力 (P): {score_result['potential']['score']} 分 (权重40%)")
        print(f"   │  └─ 详情: {score_result['potential']['details']}")
        print(f"   └─ 信息差 (I): {score_result['intelligence_gap']['score']} 分 (权重20%)")
        print(f"      └─ 详情: {score_result['intelligence_gap']['details']}")

        # 验证算法公式
        print("\n🧮 算法验证:")
        calculated_total = (
            score_result['competition']['score'] * 0.4 +
            score_result['potential']['score'] * 0.4 +
            score_result['intelligence_gap']['score'] * 0.2
        )
        print(f"   计算值: {calculated_total:.1f}")
        print(f"   实际值: {score_result['total_score']}")
        print(f"   ✅ 验证通过" if abs(calculated_total - score_result['total_score']) < 0.1 else "   ❌ 验证失败")

        print("\n" + "=" * 80)
        print("商机类型分类规则:")
        print("=" * 80)
        c = score_result['competition']['score']
        p = score_result['potential']['score']
        i = score_result['intelligence_gap']['score']

        print(f"\n当前分数: C={c}, P={p}, I={i}")
        if p > 90 and c > 70:
            print("→ 类目收割型 (P极高>90, C高>70): 适合资本型卖家")
        elif i > 85:
            print("→ 技术改良型 (I极高>85): 适合工厂型卖家")
        elif c < 60 and p > 50 and i > 60:
            print("→ 长尾暴利型 (C低<60, P中>50, I高>60): 适合个人卖家")
        elif c > 80:
            print("→ 高竞争型 (C高>80): 竞争激烈，谨慎入场")
        elif p < 40:
            print("→ 低潜力型 (P低<40): 增长乏力，不建议投入")
        else:
            print("→ 综合型: 各维度均衡")

        print("\n" + "=" * 80)
        print("测试完成 ✅")
        print("=" * 80)


async def test_all_categories():
    """测试所有品类的C-P-I分数"""
    print("\n" + "=" * 80)
    print("全品类C-P-I分数测试")
    print("=" * 80)

    categories = [
        'wireless_earbuds', 'phone_chargers', 'phone_cases', 'bluetooth_speakers',
        'desk_lamps', 'smart_plugs', 'keyboards', 'mouse', 'fitness_trackers',
        'yoga_mats', 'coffee_makers', 'webcams'
    ]

    async with AsyncSessionLocal() as db:
        results = []

        for category in categories:
            result = await db.execute(
                select(Card)
                .where(Card.category == category)
                .where(Card.amazon_data.isnot(None))
                .limit(1)
            )
            card = result.scalar_one_or_none()

            if card:
                score_result = await opportunity_scorer.calculate_opportunity_score(card, db)
                results.append({
                    'category': category,
                    'total_score': score_result['total_score'],
                    'opportunity_type': score_result['opportunity_type'],
                    'c': score_result['competition']['score'],
                    'p': score_result['potential']['score'],
                    'i': score_result['intelligence_gap']['score']
                })

        # 按总分排序
        results.sort(key=lambda x: x['total_score'], reverse=True)

        print(f"\n{'品类':<20} {'综合分':<8} {'商机类型':<15} {'C':<6} {'P':<6} {'I':<6}")
        print("-" * 80)

        for r in results:
            print(f"{r['category']:<20} {r['total_score']:<8.1f} {r['opportunity_type']:<15} {r['c']:<6.1f} {r['p']:<6.1f} {r['i']:<6.1f}")

        print("\n" + "=" * 80)
        print(f"共测试 {len(results)} 个品类")
        print(f"最高分: {results[0]['category']} ({results[0]['total_score']:.1f}分)")
        print(f"最低分: {results[-1]['category']} ({results[-1]['total_score']:.1f}分)")
        print("=" * 80)


if __name__ == "__main__":
    # 运行单个品类测试
    asyncio.run(test_cpi_algorithm())

    # 运行全品类测试
    asyncio.run(test_all_categories())
