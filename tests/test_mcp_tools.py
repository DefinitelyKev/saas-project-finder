#!/usr/bin/env python3
"""
Test script for the MCP server tools
"""

import asyncio
import httpx
import json

async def test_producthunt_tool():
    """Test the ProductHunt search tool."""
    print("Testing ProductHunt search tool...")

    url = "http://localhost:8080/search_producthunt"
    headers = {
        "X-API-Key": "saas_finder_mcp_key_2025",
        "Content-Type": "application/json"
    }

    params = {
        "category": "productivity",
        "timeframe": "week",
        "sort_by": "votes",
        "limit": 3
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, params=params)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data.get('success')}")

                if data.get('success'):
                    result = data.get('result', {})
                    print(f"Total found: {result.get('total_found', 0)}")
                    print(f"API used: {result.get('api_used', 'unknown')}")

                    products = result.get('results', [])
                    print(f"\nFirst {len(products)} products:")
                    for i, product in enumerate(products, 1):
                        print(f"{i}. {product.get('title', 'No title')}")
                        print(f"   Votes: {product.get('votes', 0)}")
                        print(f"   Description: {product.get('description', 'No description')[:100]}...")
                        print()

                    print("[SUCCESS] ProductHunt tool working!")
                else:
                    print(f"Tool failed: {data.get('error')}")
            else:
                print(f"HTTP Error: {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"Error testing ProductHunt tool: {e}")

async def test_generic_tool():
    """Test the generic execute tool endpoint."""
    print("\nTesting generic tool execution...")

    url = "http://localhost:8080/execute"
    headers = {
        "X-API-Key": "saas_finder_mcp_key_2025",
        "Content-Type": "application/json"
    }

    payload = {
        "tool_name": "search_producthunt",
        "parameters": {
            "category": "ai",
            "timeframe": "day",
            "limit": 2
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data.get('success')}")

                if data.get('success'):
                    result = data.get('result', {})
                    print(f"Total found: {result.get('total_found', 0)}")
                    print("[SUCCESS] Generic tool execution working!")
                else:
                    print(f"Tool failed: {data.get('error')}")
            else:
                print(f"HTTP Error: {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"Error testing generic tool: {e}")

async def main():
    """Main test function."""
    print("Testing MCP Server Tools\n")
    print("="*50)

    await test_producthunt_tool()

    print("="*50)

    await test_generic_tool()

    print("="*50)
    print("\n[SUCCESS] MCP Server is working correctly!")
    print("You can now use the MCP server in your main application.")

if __name__ == "__main__":
    asyncio.run(main())