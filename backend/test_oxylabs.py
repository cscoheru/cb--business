#!/usr/bin/env python3
"""测试 Oxylabs API 集成"""
import asyncio
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.products.oxylabs_client import OxylabsClient


async def main():
    """测试 Oxylabs API"""
    client = OxylabsClient()

    print("=" * 60)
    print("Oxylabs API 测试")
    print("=" * 60)

    try:
        # 测试 1: 获取 Amazon 产品
        print("\n[测试 1] 获取 Amazon 产品详情...")
        product = await client.get_amazon_product('B07FZ8S74R')

        if product:
            print(f"  ✅ 标题: {product.get('title', 'N/A')[:60]}...")
            print(f"  ✅ 品牌: {product.get('brand', 'N/A')}")
            print(f"  ✅ 评分: {product.get('rating', 0)}/5")
            print(f"  ✅ 评论数: {product.get('reviews_count', 0):,}")
            print(f"  ✅ 价格: ${product.get('price', 0)}")
            print(f"  ✅ 图片数: {len(product.get('images', []))}")
            print(f"  ✅ 特性点: {len(product.get('bullet_points', []))}")
        else:
            print("  ❌ 未找到产品")

        # 测试 2: Google 搜索
        print("\n[测试 2] Google 搜索...")
        search = await client.google_search('adidas')

        organic = search.get('results', {}).get('organic', []) if isinstance(search.get('results'), dict) else []
        knowledge = search.get('results', {}).get('knowledge', {}) if isinstance(search.get('results'), dict) else {}

        print(f"  ✅ 搜索结果: {len(search.get('results', {}).get('organic', []) if isinstance(search.get('results'), dict) else [])} 条")

        if knowledge:
            factoids = knowledge.get('factoids', [])
            if factoids:
                for f in factoids[:2]:
                    print(f"     - {f.get('title', '')}: {f.get('content', '')}")

        # 测试 3: Amazon 搜索
        print("\n[测试 3] Amazon 搜索...")
        products = await client.search_amazon('wireless charger', limit=5)

        # 处理不同的返回格式
        if isinstance(products, dict):
            products_list = products.get('results', products.get('products', []))
        else:
            products_list = products if isinstance(products, list) else []

        print(f"  ✅ 找到: {len(products_list)} 个产品")

        if products_list:
            for i, p in enumerate(products_list[:3], 1):
                title = p.get('title', p.get('name', 'N/A'))
                print(f"     {i}. {str(title)[:50]}...")

        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await client.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
