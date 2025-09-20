#!/usr/bin/env python3
"""
Simple test script to verify ProductHunt API integration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.ai.mcp_tools import MCPToolExecutor


async def test_producthunt_integration():
    """Test the ProductHunt API integration."""

    print("Testing ProductHunt API integration...")

    # Create MCP tool executor
    executor = MCPToolExecutor()

    try:
        # Test parameters
        test_params = {
            "category": "productivity",
            "timeframe": "week",
            "sort_by": "votes",
            "limit": 5
        }

        print(f"Making request with parameters: {test_params}")

        # Call the ProductHunt search
        result = await executor._search_producthunt(test_params)

        print(f"\nResults:")
        print(f"Total found: {result.get('total_found', 0)}")
        print(f"API used: {result.get('api_used', 'unknown')}")
        print(f"Category: {result.get('category')}")
        print(f"Timeframe: {result.get('timeframe')}")

        # Show first few results
        results = result.get("results", [])
        if results:
            print(f"\nFirst {min(3, len(results))} results:")
            for i, product in enumerate(results[:3], 1):
                print(f"\n{i}. {product.get('title', 'No title')}")
                print(f"   Description: {product.get('description', 'No description')}")
                print(f"   Votes: {product.get('votes', 0)}")
                print(f"   Comments: {product.get('comments', 0)}")
                print(f"   Engagement Score: {product.get('engagement_score', 0)}")
                print(f"   URL: {product.get('url', 'No URL')}")
                print(f"   Tags: {product.get('tags', [])}")
        else:
            print("No results returned")

        # Check if we're using real API or mock
        if result.get('api_used') == 'producthunt_graphql':
            print("\n[SUCCESS] Using real ProductHunt API!")
        elif result.get('api_used') == 'mock_fallback':
            print("\n[WARNING] Using mock data fallback")
        else:
            print("\n[UNKNOWN] API source unclear")

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        await executor.close()


if __name__ == "__main__":
    asyncio.run(test_producthunt_integration())