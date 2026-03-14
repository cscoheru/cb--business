#!/usr/bin/env python3
"""测试不同的 Oxylabs 源"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.products.oxylabs_client import OxylabsClient


async def main():
    """测试不同源"""
    client = OxylabsClient()

    try:
        # 测试 1: amazon_product (已知可以工作)
        print("=" * 60)
        print("[测试 1] amazon_product - 已知可以工作")
        print("=" * 60)
        try:
            product = await client.get_amazon_product('B07FZ8S74R')
            print(f"✅ 产品标题: {product.get('title', 'N/A')[:60]}")
        except Exception as e:
            print(f"❌ 错误: {e}")

        # 测试 2: amazon_search
        print("\n" + "=" * 60)
        print("[测试 2] amazon_search - 测试搜索")
        print("=" * 60)
        try:
            products = await client.search_amazon('wireless headphones', limit=3)
            print(f"✅ 返回类型: {type(products)}")
            print(f"✅ 产品数量: {len(products)}")
            if products:
                print(f"✅ 第一个产品类型: {type(products[0])}")
                if isinstance(products[0], dict):
                    print(f"✅ 第一个产品键: {list(products[0].keys())[:5]}")
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()

        # 测试 3: 直接测试 amazon_bestsellers 源
        print("\n" + "=" * 60)
        print("[测试 3] amazon_bestsellers - 原始请求")
        print("=" * 60)
        try:
            payload = {
                "source": "amazon_bestsellers",
                "domain": "com",
                "category": "electronics",
                "parse": True,
                "limit": 2
            }
            data = await client._request(payload)
            print(f"✅ 响应结构:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
        except Exception as e:
            print(f"❌ 错误: {e}")

    except Exception as e:
        print(f"全局错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
