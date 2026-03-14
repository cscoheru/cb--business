#!/usr/bin/env python3
"""
Phase 0 Day 2: Oxylabs Amazon Product Data Fetcher

Fetches real Amazon product data for market analysis.
Focus: Wireless Earbuds, Smart Plugs, Fitness Trackers
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import time

# Oxylabs Credentials - Correct format: username.password
OXYLABS_USERNAME = "fisher_VEpfJ.kCtsXux5mL~JX"
OXYLABS_PASSWORD = ""  # Empty when using combined format

# Output directory
OUTPUT_DIR = "/Users/kjonekong/Documents/cb-Business/docs/phase-0-data"


class AmazonProductFetcher:
    """Fetch Amazon product data using Oxylabs E-Commerce API"""

    def __init__(self):
        # Oxylabs API credentials format: username.password
        # Use the combined format as username, password can be empty
        self.credentials = (OXYLABS_USERNAME, OXYLABS_PASSWORD)
        self.base_url = "https://realtime.oxylabs.io/v1/queries"

    def search_products(
        self,
        query: str,
        domain: str = "amazon.com",
        pages: int = 1,
        parse: bool = True
    ) -> Dict:
        """
        Search Amazon products

        Args:
            query: Search query (e.g., "wireless earbuds")
            domain: Amazon domain (default: amazon.com)
            pages: Number of pages to fetch
            parse: Whether to use parsed response

        Returns:
            API response as dictionary
        """

        payload = {
            "source": "amazon_search",
            "query": query,
            "parse": parse,
            "geo_location": "United States",
            "pages": pages
        }

        headers = {
            "Content-Type": "application/json",
        }

        try:
            print(f"🔍 Fetching Amazon search: '{query}'...")
            response = requests.post(
                self.base_url,
                auth=self.credentials,
                json=payload,
                headers=headers,
                timeout=120
            )

            if response.status_code == 200:
                print(f"✅ Successfully fetched data for '{query}'")
                return response.json()
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return {"error": response.text}

        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
            return {"error": str(e)}

    def get_product_reviews(self, asin: str, domain: str = "amazon.com") -> Dict:
        """
        Fetch reviews for a specific product

        Args:
            asin: Amazon ASIN
            domain: Amazon domain

        Returns:
            Reviews data
        """

        payload = {
            "source": "amazon_product_reviews",
            "query": asin,
            "parse": True,
            "geo_location": "United States"
        }

        headers = {
            "Content-Type": "application/json",
        }

        try:
            print(f"📝 Fetching reviews for ASIN: {asin}...")
            response = requests.post(
                self.base_url,
                auth=self.credentials,
                json=payload,
                headers=headers,
                timeout=120
            )

            if response.status_code == 200:
                print(f"✅ Successfully fetched reviews for {asin}")
                return response.json()
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return {"error": response.text}

        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
            return {"error": str(e)}

    def extract_key_insights(self, product_data: Dict) -> Dict:
        """
        Extract key insights from product search results

        Args:
            product_data: Raw API response

        Returns:
            Structured insights dictionary
        """

        insights = {
            "timestamp": datetime.now().isoformat(),
            "products": [],
            "price_analysis": {
                "min": None,
                "max": None,
                "avg": None
            },
            "rating_analysis": {
                "min": None,
                "max": None,
                "avg": None
            },
            "brand_distribution": {}
        }

        # Try to extract products from response
        results = product_data.get("results", [])

        if not results:
            print("⚠️ No results found in API response")
            return insights

        for result in results:
            # Handle different response structures
            content = result.get("content", {})

            if "organic" in content:
                products = content["organic"]
            elif "results" in content:
                products = content["results"]
            else:
                products = []

            prices = []
            ratings = []

            for product in products[:20]:  # Limit to top 20
                try:
                    product_info = {
                        "title": product.get("title", "N/A")[:100],
                        "asin": product.get("asin", "N/A"),
                        "price": None,
                        "rating": None,
                        "reviews_count": None,
                        "url": product.get("url", ""),
                        "brand": product.get("brand", "Unknown")
                    }

                    # Extract price
                    price_obj = product.get("price", {})
                    if isinstance(price_obj, dict):
                        product_info["price"] = price_obj.get("current")
                    elif isinstance(price_obj, (int, float, str)):
                        product_info["price"] = price_obj

                    # Extract rating
                    rating_obj = product.get("rating", {})
                    if isinstance(rating_obj, dict):
                        product_info["rating"] = rating_obj.get("value")
                    elif isinstance(rating_obj, (int, float)):
                        product_info["rating"] = rating_obj

                    # Extract review count
                    reviews_count = product.get("reviews_count", 0)
                    product_info["reviews_count"] = reviews_count

                    # Collect for analysis
                    if product_info["price"]:
                        try:
                            prices.append(float(str(product_info["price"]).replace("$", "")))
                        except:
                            pass

                    if product_info["rating"]:
                        try:
                            ratings.append(float(product_info["rating"]))
                        except:
                            pass

                    # Brand distribution
                    brand = product_info.get("brand", "Unknown")
                    insights["brand_distribution"][brand] = \
                        insights["brand_distribution"].get(brand, 0) + 1

                    insights["products"].append(product_info)

                except Exception as e:
                    print(f"⚠️ Error parsing product: {e}")
                    continue

            # Calculate statistics
            if prices:
                insights["price_analysis"] = {
                    "min": round(min(prices), 2),
                    "max": round(max(prices), 2),
                    "avg": round(sum(prices) / len(prices), 2)
                }

            if ratings:
                insights["rating_analysis"] = {
                    "min": round(min(ratings), 2),
                    "max": round(max(ratings), 2),
                    "avg": round(sum(ratings) / len(ratings), 2)
                }

        return insights

    def save_results(self, data: Dict, filename: str):
        """Save results to JSON file"""

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved to: {filepath}")

    def run_all_searches(self):
        """Execute all search queries for Phase 0"""

        print("=" * 60)
        print("PHASE 0 DAY 2: Amazon Data Collection")
        print("=" * 60)

        searches = [
            # Category 1: Wireless Earbuds
            "wireless earbuds bluetooth",
            "noise cancelling earbuds",
            "true wireless earbuds",

            # Category 2: Smart Plugs
            "smart plug wifi",
            "smart home plug",
            "amazon smart plug",

            # Category 3: Fitness Trackers
            "fitness tracker watch",
            "smart band fitness",
            "activity tracker"
        ]

        all_results = {
            "search_timestamp": datetime.now().isoformat(),
            "categories": {}
        }

        for query in searches:
            print(f"\n{'─' * 50}")
            print(f"Search: {query}")
            print(f"{'─' * 50}")

            # Fetch data
            raw_data = self.search_products(query)

            if "error" in raw_data:
                print(f"⚠️ Skipping {query} due to error")
                continue

            # Extract insights
            insights = self.extract_key_insights(raw_data)

            # Save individual result
            filename = f"amazon_{query.replace(' ', '_')}.json"
            self.save_results(insights, filename)

            # Add to collection
            category_key = query.split()[0]  # First word as category
            all_results["categories"][category_key] = insights

            # Rate limiting
            time.sleep(2)

        # Save combined results
        self.save_results(all_results, "amazon_all_searches.json")

        print("\n" + "=" * 60)
        print("✅ All searches completed!")
        print("=" * 60)

        return all_results


def main():
    """Main execution"""

    fetcher = AmazonProductFetcher()

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  Phase 0 Day 2: Amazon Product Data Fetcher             ║
    ║  Using Oxylabs E-Commerce API                           ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Run all searches
    results = fetcher.run_all_searches()

    # Print summary
    print("\n📊 SUMMARY:")
    for category, data in results.get("categories", {}).items():
        products = len(data.get("products", []))
        price_avg = data.get("price_analysis", {}).get("avg", "N/A")
        rating_avg = data.get("rating_analysis", {}).get("avg", "N/A")

        print(f"  • {category}: {products} products, "
              f"Avg Price: ${price_avg}, Avg Rating: {rating_avg}")

    print(f"\n💾 All data saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
