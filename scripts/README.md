# Scripts Directory

Executable scripts for the SaaS Project Finder system.

## MCP Server Script

### `simple_mcp_server.py`
Standalone MCP server for manual development use.

```bash
# Manual start (for development only)
./venv-python scripts/simple_mcp_server.py
# Server runs on http://localhost:8080
```

**Note:** The MCP server starts automatically with `docker-compose up --build`. This script is only needed for manual development testing.

**Features:**
- RESTful API endpoints
- API key authentication
- Automatic fallback to local execution

**Endpoints:**
- `GET /health` - Health check
- `POST /execute` - Generic tool execution
- `POST /search_producthunt` - ProductHunt search

## Configuration

Scripts use configuration from `.env`:

```bash
MCP_SERVER_URL=http://localhost:8080
MCP_API_KEY=saas_finder_mcp_key_2025
PRODUCTHUNT_API_TOKEN=your_token
```

## Development Workflow

```bash
# Normal development (MCP server included)
docker-compose up --build

# Manual MCP server for debugging
./venv-python scripts/simple_mcp_server.py

# Test integration
./venv-python tests/test_mcp_server.py
```

## Troubleshooting

**Port in use:**
```bash
lsof -i :8080  # Find process
kill -9 <PID>  # Kill process
```

**Permission errors:**
```bash
chmod +x scripts/*.py
```