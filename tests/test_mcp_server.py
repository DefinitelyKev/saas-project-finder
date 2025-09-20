#!/usr/bin/env python3
"""
Test script for the MCP server
"""

import asyncio
import httpx
import json
import sys

async def test_http_server():
    """Test the HTTP MCP server."""
    print("Testing MCP HTTP Server...")

    base_url = "http://localhost:8080"
    headers = {
        "X-API-Key": "saas_finder_mcp_key_2025",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            # Test health check
            print("1. Testing health check...")
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
                print("   [SUCCESS] Health check passed")
            else:
                print("   [FAILED] Health check failed")

            # Test server info
            print("\n2. Testing server info...")
            response = await client.get(f"{base_url}/info")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                info = response.json()
                print(f"   Server: {info.get('name')}")
                print(f"   Version: {info.get('version')}")
                print(f"   Tools: {', '.join(info.get('tools', []))}")
                print("   [SUCCESS] Server info retrieved")
            else:
                print("   [FAILED] Server info failed")

            print(f"\n[SUCCESS] MCP Server is running at {base_url}")
            print(f"[MCP] MCP SSE endpoint: {base_url}/sse")
            print(f"[KEY] API Key: saas_finder_mcp_key_2025")

        except httpx.ConnectError:
            print("[FAILED] Could not connect to MCP server")
            print("Make sure the server is running with:")
            print("   docker-compose up --build (includes MCP server)")
            print("   OR manually: ./venv-python scripts/simple_mcp_server.py")
            return False
        except Exception as e:
            print(f"[FAILED] Error testing server: {e}")
            return False

    return True

def test_configuration():
    """Test the configuration."""
    print("Testing configuration...")

    try:
        # Test settings import
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, os.path.join(project_root, 'src'))
        from config.settings import settings

        print(f"[SUCCESS] Settings loaded successfully")
        print(f"   MCP Server URL: {settings.mcp_server_url}")
        print(f"   MCP API Key: {settings.mcp_api_key}")
        print(f"   ProductHunt Token: {'[SUCCESS] Set' if settings.producthunt_api_token else '[FAILED] Not set'}")

        return True

    except Exception as e:
        print(f"[FAILED] Configuration error: {e}")
        return False

async def main():
    """Main test function."""
    print("[TEST] Testing SaaS Finder MCP Server Setup\n")

    # Test configuration
    config_ok = test_configuration()

    if not config_ok:
        print("\n[FAILED] Configuration tests failed")
        return

    print("\n" + "="*50)

    # Test HTTP server
    server_ok = await test_http_server()

    print("\n" + "="*50)

    if config_ok and server_ok:
        print("\n[SUCCESS] All tests passed!")
        print("\nYour MCP server is ready to use!")
        print("\nNext steps:")
        print("1. MCP server starts automatically with: docker-compose up --build")
        print("2. Your main application can now connect to http://localhost:8080")
        print("3. Use API key 'saas_finder_mcp_key_2025' for authentication")
    else:
        print("\n[FAILED] Some tests failed. Please check the output above.")

if __name__ == "__main__":
    asyncio.run(main())