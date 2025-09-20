# Tests Directory

Test scripts for the SaaS Project Finder system.

## Test Files

### `test_mcp_server.py`
Tests MCP server configuration and health.

```bash
./venv-python tests/test_mcp_server.py
```

**Tests:**
- Settings configuration loading
- Health check endpoint (`GET /health`)
- Server info endpoint (`GET /info`)
- Authentication

### `test_mcp_tools.py`
Tests MCP tools functionality and API integration.

```bash
./venv-python tests/test_mcp_tools.py
```

**Tests:**
- ProductHunt search tool
- Generic tool execution endpoint
- API response structure
- Error handling

### `test_producthunt_api.py`
Tests direct ProductHunt API integration.

```bash
./venv-python tests/test_producthunt_api.py
```

**Tests:**
- GraphQL API calls
- Token authentication
- Data parsing and validation
- Fallback behavior

## Running Tests

```bash
# Individual tests
./venv-python tests/test_mcp_server.py
./venv-python tests/test_mcp_tools.py
./venv-python tests/test_producthunt_api.py

# All tests (requires MCP server running)
./venv-python tests/test_mcp_server.py && \
./venv-python tests/test_mcp_tools.py && \
./venv-python tests/test_producthunt_api.py
```

## Prerequisites

1. **MCP Server Running** (for tools tests)
   ```bash
   ./venv-python scripts/simple_mcp_server.py
   ```

2. **Environment Configuration**
   - `.env` file with proper settings
   - `PRODUCTHUNT_API_TOKEN` for real API tests
   - `MCP_API_KEY` matching server config

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MCP server connection failed | Start server: `./venv-python scripts/simple_mcp_server.py` |
| Authentication failed | Check `MCP_API_KEY` in `.env` |
| ProductHunt API errors | Verify `PRODUCTHUNT_API_TOKEN` |
| Import errors | Run from project root |

## Manual Testing

```python
import httpx

async def manual_testing():
    # Health check
    async with httpx.AsyncClient() as client:
        health_response = await client.get("http://localhost:8080/health")
        print("Health:", health_response.json())

        # With authentication
        info_response = await client.get(
            "http://localhost:8080/info",
            headers={"X-API-Key": "saas_finder_mcp_key_2025"}
        )
        print("Info:", info_response.json())

        # Tool execution
        tool_response = await client.post(
            "http://localhost:8080/execute",
            headers={
                "X-API-Key": "saas_finder_mcp_key_2025",
                "Content-Type": "application/json"
            },
            json={
                "tool_name": "search_producthunt",
                "parameters": {"limit": 1}
            }
        )
        print("Tool result:", tool_response.json())
```