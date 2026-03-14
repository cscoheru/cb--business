#!/usr/bin/env python3
"""测试 Oxylabs 原始响应格式"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.products.oxylabs_client import OxylabsClient


async def main():
    """测试原始响应格式"""
    client = OxylabsClient()

    try:
        # 直接调用 _request 查看原始响应
        payload = {
            "source": "amazon_bestsellers",
            "domain": "com",
            "category": "electronics",
            "parse": True,
            "limit": 2
        }

        print("发送请求到 Oxylabs API...")
        data = await client._request(payload)

        print(f"\n响应类型: {type(data)}")
        print(f"顶层键: {list(data.keys())}")

        if "results" in data:
            results = data["results"]
            print(f"\nresults 类型: {type(results)}")
            print(f"results 长度: {len(results)}")

            print(f"\nresults[0] 类型: {type(results[0])}")

            if isinstance(results[0], dict):
                print(f"results[0] 键: {list(results[0].keys())}")
                print(f"\n完整响应结构:")
                print(json.dumps(results[0], indent=2, ensure_ascii=False)[:2000])
            elif isinstance(results[0], list):
                print(f"results[0] 是列表")
                print(f"results[0] 内容: {results[0]}")
            else:
                print(f"results[0] 是其他类型: {results[0]}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
