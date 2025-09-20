# API Communication Standards

This document defines the required standards for all API interactions and code examples in the SaaS Project Finder system.

## Core Requirements

### HTTP Operations
- **NEVER use curl commands** in any documentation or examples
- **ALWAYS use Python with httpx** for API interactions
- **ALWAYS use async/await patterns** for HTTP operations
- **ALWAYS use httpx.AsyncClient()** context manager

### Code Formatting
- **NEVER include emojis** in code examples, outputs, or logs
- **Use plain text** for all technical communication
- **Focus on functionality** over visual formatting
- **Keep examples clean and professional**

## Standard Python HTTP Pattern

```python
import asyncio
import httpx

async def api_example():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/endpoint",
            headers={
                "X-API-Key": "your-api-key",
                "Content-Type": "application/json"
            },
            json={"parameter": "value"}
        )
        return response.json()

# Execute
result = asyncio.run(api_example())
```

## Examples

### Good Examples (Follow These)

**Tenant Registration:**
```python
import asyncio
import httpx

async def register_tenant():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/register",
            headers={"Content-Type": "application/json"},
            json={
                "name": "Test Company",
                "tier": "free",
                "allowed_agents": ["customer-support"]
            }
        )
        return response.json()
```

**Agent Execution:**
```python
async def execute_agent():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/agents/saas-trend-scanner/execute",
            headers={
                "X-API-Key": "your-key",
                "Content-Type": "application/json"
            },
            json={
                "parameters": {
                    "scan_platforms": ["producthunt", "reddit"],
                    "volume_target": "high-volume"
                }
            }
        )
        return response.json()
```

**Health Check:**
```python
async def health_check():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        return response.json()
```

### Bad Examples (Never Use These)

**Never use curl:**
```bash
# WRONG - Never use this
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Company"}'
```

**Never include emojis:**
```python
# WRONG - Never include emojis
print("Starting scan... 🚀")
logger.info("Scan complete! ✅")
```

**Never use sync requests:**
```python
# WRONG - Never use sync httpx
import httpx
response = httpx.post("http://localhost:8000/api/endpoint")
```

## Enforcement

These standards are strictly enforced:
- All documentation must use Python examples
- All code must pass without emojis
- All HTTP operations must be async
- All examples must be complete and runnable

## Rationale

1. **Consistency**: Python-first approach matches the codebase
2. **Professional**: No emojis in technical documentation
3. **Performance**: Async operations are more efficient
4. **Integration**: Examples can be directly used in code
5. **Compatibility**: Avoids shell/curl dependency issues