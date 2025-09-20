#!/usr/bin/env python3
"""
Simple HTTP-based MCP-compatible server for SaaS Project Finder
Provides tools for discovering and analyzing SaaS ideas from various platforms.
"""

import asyncio
import logging
import sys
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# FastAPI and HTTP imports
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Project imports
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from infrastructure.ai.mcp_tools import MCPToolExecutor
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API
class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class ToolResponse(BaseModel):
    success: bool
    result: Any
    error: Optional[str] = None
    timestamp: str

class SaaSFinderMCPServer:
    """Simple HTTP MCP-compatible server for SaaS Project Finder tools."""

    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.executor = None

        # Create FastAPI app
        self.app = FastAPI(
            title="SaaS Project Finder MCP Server",
            description="HTTP API for SaaS project discovery and analysis tools",
            version="1.0.0"
        )

        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """Setup middleware for the FastAPI app."""

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _verify_api_key(self, x_api_key: str = Header(...)):
        """Verify the API key."""
        expected_key = settings.mcp_api_key
        if x_api_key != expected_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return x_api_key

    def _setup_routes(self):
        """Setup HTTP routes for the server."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return JSONResponse({
                "status": "healthy",
                "server": "saas-project-finder-mcp",
                "timestamp": datetime.utcnow().isoformat()
            })

        @self.app.get("/info")
        async def server_info():
            """Get server information."""
            return JSONResponse({
                "name": "saas-project-finder",
                "version": "1.0.0",
                "description": "MCP server for SaaS project discovery and analysis",
                "tools": [
                    "search_producthunt",
                    "search_reddit_startups",
                    "search_hackernews",
                    "analyze_market_size",
                    "analyze_competition",
                    "check_domain_availability",
                    "analyze_google_trends"
                ]
            })

        @self.app.post("/execute", dependencies=[Depends(self._verify_api_key)])
        async def execute_tool(request: ToolRequest) -> ToolResponse:
            """Execute an MCP tool."""

            if not self.executor:
                self.executor = MCPToolExecutor()

            try:
                result = await self.executor.execute_mcp_tool(
                    request.tool_name,
                    request.parameters
                )

                return ToolResponse(
                    success=True,
                    result=result,
                    timestamp=datetime.utcnow().isoformat()
                )

            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return ToolResponse(
                    success=False,
                    result=None,
                    error=str(e),
                    timestamp=datetime.utcnow().isoformat()
                )

        @self.app.post("/search_producthunt", dependencies=[Depends(self._verify_api_key)])
        async def search_producthunt(
            category: str = "productivity",
            timeframe: str = "week",
            sort_by: str = "votes",
            limit: int = 20
        ) -> ToolResponse:
            """Search ProductHunt for trending products and ideas."""

            if not self.executor:
                self.executor = MCPToolExecutor()

            try:
                result = await self.executor._search_producthunt({
                    "category": category,
                    "timeframe": timeframe,
                    "sort_by": sort_by,
                    "limit": limit
                })

                return ToolResponse(
                    success=True,
                    result=result,
                    timestamp=datetime.utcnow().isoformat()
                )

            except Exception as e:
                logger.error(f"ProductHunt search failed: {e}")
                return ToolResponse(
                    success=False,
                    result=None,
                    error=str(e),
                    timestamp=datetime.utcnow().isoformat()
                )

        @self.app.post("/search_reddit_startups", dependencies=[Depends(self._verify_api_key)])
        async def search_reddit_startups(
            subreddit: str = "startups",
            keywords: List[str] = None,
            timeframe: str = "week",
            sort_by: str = "hot"
        ) -> ToolResponse:
            """Search Reddit startup communities for SaaS ideas and discussions."""

            if not self.executor:
                self.executor = MCPToolExecutor()

            try:
                result = await self.executor._search_reddit_startups({
                    "subreddit": subreddit,
                    "keywords": keywords or [],
                    "timeframe": timeframe,
                    "sort_by": sort_by
                })

                return ToolResponse(
                    success=True,
                    result=result,
                    timestamp=datetime.utcnow().isoformat()
                )

            except Exception as e:
                logger.error(f"Reddit search failed: {e}")
                return ToolResponse(
                    success=False,
                    result=None,
                    error=str(e),
                    timestamp=datetime.utcnow().isoformat()
                )

        @self.app.post("/analyze_market_size", dependencies=[Depends(self._verify_api_key)])
        async def analyze_market_size(
            industry: str,
            target_audience: str = "",
            keywords: List[str] = None,
            geographic_scope: str = "global"
        ) -> ToolResponse:
            """Research and estimate market size for a SaaS idea."""

            if not self.executor:
                self.executor = MCPToolExecutor()

            try:
                result = await self.executor._analyze_market_size({
                    "industry": industry,
                    "target_audience": target_audience,
                    "keywords": keywords or [],
                    "geographic_scope": geographic_scope
                })

                return ToolResponse(
                    success=True,
                    result=result,
                    timestamp=datetime.utcnow().isoformat()
                )

            except Exception as e:
                logger.error(f"Market analysis failed: {e}")
                return ToolResponse(
                    success=False,
                    result=None,
                    error=str(e),
                    timestamp=datetime.utcnow().isoformat()
                )

    async def run(self):
        """Run the HTTP server."""
        logger.info(f"Starting SaaS Finder MCP Server on http://{self.host}:{self.port}")
        logger.info(f"Health check: http://{self.host}:{self.port}/health")
        logger.info(f"Server info: http://{self.host}:{self.port}/info")
        logger.info(f"Execute tool: POST http://{self.host}:{self.port}/execute")
        logger.info(f"API Key required: {settings.mcp_api_key}")

        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def cleanup(self):
        """Clean up resources."""
        if self.executor:
            await self.executor.close()

async def main():
    """Main entry point for the HTTP MCP server."""
    # Read host and port from environment or use defaults
    host = os.getenv("MCP_HOST", "localhost")
    port = int(os.getenv("MCP_PORT", "8080"))

    server = SaaSFinderMCPServer(host=host, port=port)

    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())