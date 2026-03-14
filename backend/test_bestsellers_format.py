#!/usr/bin/env python3
"""测试 Oxylabs Amazon Best Sellers 返回格式"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.products.oxylabs_client import OxylabsClient


async def main():
    """测试 Best Sellers 格式"""
    client = OxylabsClient()

    try:
        print("Testing Amazon Best Sellers for 'electronics'...")
        products = await client.get_amazon_bestsellers(
            category="electronics",
            domain="com",
            limit=3
        )

        print(f"\n返回类型: {type(products)}")
        print(f"返回数量: {len(products)}")

        if products:
            print(f"\n第一个产品类型: {type(products[0])}")

            if isinstance(products[0], dict):
                print(f"第一个产品的键: {list(products[0].keys())}")
                print(f"\n第一个产品数据:")
                print(json.dumps(products[0], indent=2, ensure_ascii=False)[:1000])
            else:
                print(f"第一个产品不是dict: {products[0]}")

                # 检查是否是字符串
                if isinstance(products[0], str):
                    print(f"\n第一个产品是字符串: {products[0][:200]}")
        else:
            print("没有返回任何产品")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
