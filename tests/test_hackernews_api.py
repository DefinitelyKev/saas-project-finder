#!/usr/bin/env python3
"""
Test script to verify Hacker News API integration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from infrastructure.ai.mcp_tools import MCPToolExecutor


async def test_hackernews_integration():
    """Test the Hacker News API integration."""

    print("Testing Hacker News API integration...")

    # Create MCP tool executor
    executor = MCPToolExecutor()

    try:
        # Test parameters for different story types
        test_cases = [
            {
                "name": "Show HN Stories",
                "params": {"query": "Show HN", "story_type": "show_hn", "limit": 5, "sort_by": "points"},
            },
            {
                "name": "Ask HN Stories",
                "params": {"query": "SaaS", "story_type": "ask_hn", "limit": 3, "sort_by": "comments"},
            },
            {
                "name": "AI-related Show HN",
                "params": {"query": "AI", "story_type": "show_hn", "limit": 3, "sort_by": "engagement"},
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing {test_case['name']}...")
            print(f"   Parameters: {test_case['params']}")

            try:
                # Call the Hacker News search
                result = await executor._search_hackernews(test_case["params"])

                print(f"   Results found: {result.get('total_found', 0)}")
                print(f"   API used: {result.get('api_used', 'unknown')}")
                print(f"   Query: {result.get('query')}")
                print(f"   Story type: {result.get('story_type')}")

                # Show first few results
                results = result.get("results", [])
                if results:
                    print(f"   First {min(2, len(results))} results:")
                    for j, story in enumerate(results[:2], 1):
                        print(f"     {j}. {story.get('title', 'No title')}")
                        print(f"        Points: {story.get('points', 0)}")
                        print(f"        Comments: {story.get('comments', 0)}")
                        print(f"        Author: {story.get('author', 'unknown')}")
                        print(f"        Engagement Score: {story.get('engagement_score', 0)}")
                        print(f"        SaaS Keywords: {story.get('saas_keywords', [])}")
                        print(f"        URL: {story.get('url', 'No URL')}")
                        if story.get("external_url"):
                            print(f"        External URL: {story.get('external_url')}")
                else:
                    print("   No results returned")

                # Check API source
                if result.get("api_used") == "hackernews_official":
                    print("   [SUCCESS] Using real Hacker News API!")
                elif result.get("api_used") == "mock_fallback":
                    print("   [WARNING] Using mock data fallback")
                    if result.get("error"):
                        print(f"   [ERROR] API error: {result.get('error')}")
                else:
                    print("   [UNKNOWN] API source unclear")

            except Exception as e:
                print(f"   [ERROR] Test case failed: {str(e)}")
                import traceback

                traceback.print_exc()

        print(f"\n[SUCCESS] Hacker News API integration test completed")
        print(f"[INFO] Hacker News API provides:")
        print(f"  - Show HN posts (great for SaaS project discovery)")
        print(f"  - Ask HN discussions (market research and feedback)")
        print(f"  - Job postings (startup hiring insights)")
        print(f"  - Real-time data with no authentication required")
        print(f"  - Engagement metrics (points, comments)")
        print(f"  - SaaS keyword extraction for better filtering")

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up
        await executor.close()


if __name__ == "__main__":
    asyncio.run(test_hackernews_integration())
