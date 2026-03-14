#!/usr/bin/env python3
"""插入测试卡片到数据库"""
import asyncio
import sys
from datetime import datetime, timezone
from sqlalchemy import select
from config.database import AsyncSessionLocal, engine
from models.card import Card

# 测试卡片数据
test_cards = [
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "title": "无线耳机市场洞察 - 实时生成",
        "category": "wireless_earbuds",
        "content": {
            "summary": {
                "title": "无线耳机",
                "opportunity_score": 85,
                "market_size": 16,
                "sweet_spot": {"min": 20, "max": 30, "best": 25},
                "reliability": 0.95
            },
            "insights": {
                "top_products": [{
                    "asin": "B0B66CJZL5",
                    "price": 19.99,
                    "title": "Anker P20i True Wireless",
                    "rating": 4.6,
                    "reviews_count": 97900
                }],
                "price_sweet_spot": {"min": 20, "max": 30, "best": 25},
                "market_saturation": "high",
                "trend_strength": "medium"
            },
            "market_data": {
                "price": {"avg": 32, "min": 15, "max": 80, "count": 16},
                "rating": {"avg": 4.3, "min": 3.8, "max": 4.7, "count": 14},
                "trend_analysis": {"total_trends": 5, "avg_volume": 45}
            },
            "recommendations": [
                "目标价格: $25-35",
                "核心卖点: 防丢失设计 + 稳定连接",
                "差异化: 不拼高端ANC，专注解决用户痛点"
            ],
            "data_sources": ["Amazon API", "Google Trends"],
            "generated_at": datetime.now(timezone.utc).isoformat()
        },
        "analysis": {
            "category": "wireless_earbuds",
            "category_name": "无线耳机",
            "opportunity_score": 85
        },
        "amazon_data": {
            "products": [{
                "asin": "B0B66CJZL5",
                "title": "Anker P20i True Wireless",
                "price": 19.99,
                "rating": 4.6,
                "reviews_count": 97900
            }]
        }
    },
    {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "title": "智能插座市场洞察 - 实时生成",
        "category": "smart_plugs",
        "content": {
            "summary": {
                "title": "智能插座",
                "opportunity_score": 72,
                "market_size": 14,
                "sweet_spot": {"min": 20, "max": 30, "best": 25},
                "reliability": 0.95
            },
            "insights": {
                "top_products": [{
                    "asin": "B08R6WK6W8",
                    "price": 14.99,
                    "title": "Kasa Smart Plug HS103P",
                    "rating": 4.6,
                    "reviews_count": 285000
                }],
                "price_sweet_spot": {"min": 20, "max": 30, "best": 25},
                "market_saturation": "high",
                "trend_strength": "medium"
            },
            "market_data": {
                "price": {"avg": 26, "min": 12, "max": 45, "count": 14},
                "rating": {"avg": 4.3, "min": 3.9, "max": 4.6, "count": 12},
                "trend_analysis": {"total_trends": 3, "avg_volume": 35}
            },
            "recommendations": [
                "目标价格: $20-30",
                "核心功能: 能耗监测 + 多插座设计",
                "差异化: 避免纯价格竞争"
            ],
            "data_sources": ["Amazon API", "Google Trends"],
            "generated_at": datetime.now(timezone.utc).isoformat()
        },
        "analysis": {
            "category": "smart_plugs",
            "category_name": "智能插座",
            "opportunity_score": 72
        },
        "amazon_data": {
            "products": [{
                "asin": "B08R6WK6W8",
                "title": "Kasa Smart Plug HS103P",
                "price": 14.99,
                "rating": 4.6,
                "reviews_count": 285000
            }]
        }
    },
    {
        "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "title": "健身追踪器市场洞察 - 实时生成",
        "category": "fitness_trackers",
        "content": {
            "summary": {
                "title": "健身追踪器",
                "opportunity_score": 78,
                "market_size": 18,
                "sweet_spot": {"min": 30, "max": 50, "best": 45},
                "reliability": 0.95
            },
            "insights": {
                "top_products": [{
                    "asin": "B0BPHHZ6HS",
                    "price": 79.95,
                    "title": "Fitbit Inspire 3",
                    "rating": 4.6,
                    "reviews_count": 18500
                }],
                "price_sweet_spot": {"min": 30, "max": 50, "best": 45},
                "market_saturation": "medium",
                "trend_strength": "high"
            },
            "market_data": {
                "price": {"avg": 58, "min": 25, "max": 150, "count": 18},
                "rating": {"avg": 4.2, "min": 3.7, "max": 4.7, "count": 16},
                "trend_analysis": {"total_trends": 8, "avg_volume": 65}
            },
            "recommendations": [
                "目标价格: $40-60 (中端) 或 $20-30 (预算)",
                "核心功能: 长续航 (+2周) + 健康监测",
                "差异化: 避免与Apple/Samsung正面竞争"
            ],
            "data_sources": ["Amazon API", "Google Trends"],
            "generated_at": datetime.now(timezone.utc).isoformat()
        },
        "analysis": {
            "category": "fitness_trackers",
            "category_name": "健身追踪器",
            "opportunity_score": 78
        },
        "amazon_data": {
            "products": [{
                "asin": "B0BPHHZ6HS",
                "title": "Fitbit Inspire 3",
                "price": 79.95,
                "rating": 4.6,
                "reviews_count": 18500
            }]
        }
    }
]


async def insert_test_cards():
    """插入测试卡片"""
    print("开始插入测试卡片...")

    async with AsyncSessionLocal() as session:
        for card_data in test_cards:
            # 检查是否已存在
            existing = await session.execute(
                select(Card).where(Card.id == card_data["id"])
            )
            if existing.scalar_one_or_none():
                print(f"  跳过已存在的卡片: {card_data['id']}")
                continue

            # 创建新卡片
            card = Card(
                id=card_data["id"],
                title=card_data["title"],
                category=card_data["category"],
                content=card_data["content"],
                analysis=card_data["analysis"],
                amazon_data=card_data["amazon_data"],
                is_published=True,
                created_at=datetime.now(timezone.utc),
                published_at=datetime.now(timezone.utc),
                views=0,
                likes=0
            )

            session.add(card)
            print(f"  添加卡片: {card_data['title']}")

        await session.commit()
        print("✅ 测试卡片插入成功！")


async def main():
    """主函数"""
    try:
        await insert_test_cards()

        # 验证插入
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Card).where(Card.is_published == True)
            )
            cards = result.scalars().all()
            print(f"\n当前数据库中有 {len(cards)} 张已发布的卡片")
            for card in cards:
                print(f"  - {card.title} ({card.category})")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
