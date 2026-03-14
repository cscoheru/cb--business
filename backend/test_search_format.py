#!/usr/bin/env python3
"""检查 amazon_search 返回格式"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.products.oxylabs_client import OxylabsClient


async def main():
    """检查搜索返回格式"""
    client = OxylabsClient()

    try:
        print("Testing amazon_search for 'wireless headphones'...")
        result = await client.search_amazon('wireless headphones', limit=3)

        print(f"\n返回类型: {type(result)}")

        if isinstance(result, dict):
            print(f"Dict 键: {list(result.keys())}")

            for key, value in result.items():
                if isinstance(value, list):
                    print(f"\n{key} (list): {len(value)} 项")
                    if value:
                        print(f"  第一项类型: {type(value[0])}")
                        if isinstance(value[0], dict):
                            print(f"  第一项键: {list(value[0].keys())[:10]}")
                            print(f"\n  示例产品:")
                            print(json.dumps(value[0], indent=2, ensure_ascii=False)[:800])
                else:
                    print(f"\n{key}: {type(value)} = {str(value)[:200]}")
        elif isinstance(result, list):
            print(f"\nList 长度: {len(result)}")
            if result:
                print(f"第一项类型: {type(result[0])}")
                if isinstance(result[0], dict):
                    print(f"第一项键: {list(result[0].keys())[:10]}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
