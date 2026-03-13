#!/usr/bin/env python3
"""
Card System Test Script
Tests the complete card generation pipeline
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import AsyncSessionLocal
from models.card import Card
from services.card_generator import CardGenerator
from sqlalchemy import select


async def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Card).limit(1))
            cards = result.scalars().all()
            print(f"✅ Database connected. Found {len(cards)} existing cards.")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_card_generation():
    """Test card generation for a single category"""
    print("\n🎨 Testing card generation...")
    generator = CardGenerator()

    try:
        # Test wireless_earbuds category
        print("  → Fetching Amazon data for wireless_earbuds...")
        products = await generator.fetch_category_data('wireless_earbuds')

        if not products:
            print("  ❌ No products returned")
            return False

        print(f"  ✅ Fetched {len(products)} products")

        # Test AI analysis
        print("  → Running AI analysis...")
        analysis = await generator.analyze_with_ai('wireless_earbuds', products)
        print(f"  ✅ Analysis complete. Opportunity score: {analysis['opportunity_score']}")

        # Test card generation
        print("  → Generating card...")
        card = await generator.generate_card('wireless_earbuds')
        print(f"  ✅ Card generated: {card.title}")
        print(f"     - Category: {card.category}")
        print(f"     - Opportunity Score: {card.content['summary']['opportunity_score']}")
        print(f"     - Price Range: ${card.content['summary']['sweet_spot']['min']} - ${card.content['summary']['sweet_spot']['max']}")

        await generator.close()
        return True

    except Exception as e:
        print(f"  ❌ Card generation failed: {e}")
        import traceback
        traceback.print_exc()
        await generator.close()
        return False


async def test_card_persistence():
    """Test saving and retrieving cards"""
    print("\n💾 Testing card persistence...")
    generator = CardGenerator()

    try:
        # Generate a test card
        card = await generator.generate_card('wireless_earbuds')

        # Save to database
        async with AsyncSessionLocal() as db:
            db.add(card)
            await db.commit()
            print(f"  ✅ Card saved to database with ID: {card.id}")

            # Retrieve the card
            result = await db.execute(select(Card).where(Card.id == card.id))
            retrieved_card = result.scalar_one_or_none()

            if retrieved_card:
                print(f"  ✅ Card retrieved successfully")
                print(f"     - Title: {retrieved_card.title}")
                print(f"     - Content keys: {list(retrieved_card.content.keys())}")
            else:
                print("  ❌ Failed to retrieve card")
                return False

        await generator.close()
        return True

    except Exception as e:
        print(f"  ❌ Persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        await generator.close()
        return False


async def test_oxylabs_connection():
    """Test Oxylabs API connection"""
    print("\n🌐 Testing Oxylabs API connection...")
    from crawler.products.oxylabs_client import OxylabsClient

    client = OxylabsClient()

    try:
        # Test a simple search
        print("  → Testing Amazon search API...")
        products = await client.search_amazon(
            query='wireless earbuds',
            limit=5,
            use_cache=False
        )

        if products:
            print(f"  ✅ Oxylabs API working. Got {len(products)} products")
            if products:
                print(f"     - First product: {products[0].get('title', 'N/A')[:50]}...")
            await client.close()
            return True
        else:
            print("  ⚠️  No products returned (API may be working but no results)")
            await client.close()
            return False

    except Exception as e:
        print(f"  ❌ Oxylabs API test failed: {e}")
        await client.close()
        return False


async def test_redis_cache():
    """Test Redis cache functionality"""
    print("\n🗄️  Testing Redis cache...")
    from services.cache import cache_service

    try:
        # Test set and get
        await cache_service.set('test', 'key', {'value': 'test_data'}, ttl=60)
        result = await cache_service.get('test', 'key')

        if result and result.get('value') == 'test_data':
            print("  ✅ Redis cache working")
            # Cleanup
            await cache_service.delete('test', 'key')
            return True
        else:
            print(f"  ❌ Cache returned unexpected result: {result}")
            return False

    except Exception as e:
        print(f"  ❌ Redis cache test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Card System Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {}

    # Run tests
    results['database'] = await test_database_connection()
    results['redis'] = await test_redis_cache()
    results['oxylabs'] = await test_oxylabs_connection()
    results['card_generation'] = await test_card_generation()
    results['persistence'] = await test_card_persistence()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
