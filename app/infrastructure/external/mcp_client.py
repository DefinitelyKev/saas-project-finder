from typing import Any, Dict, List, Optional, Union
import json
import asyncio
import structlog
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Any


@dataclass
class MCPResource:
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None


class MCPClient:
    """
    Model Context Protocol (MCP) client implementation
    Provides standardized way to connect AI models to external tools and data sources
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.servers: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize MCP client"""
        if not self.enabled:
            logger.info("MCP is disabled")
            return
        
        logger.info("Initializing MCP client")
        await self._register_default_tools()
        await self._register_default_resources()
        self._initialized = True
    
    async def _register_default_tools(self) -> None:
        """Register default MCP tools"""
        # File system operations
        await self.register_tool(
            name="read_file",
            description="Read contents of a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"}
                },
                "required": ["path"]
            },
            handler=self._handle_read_file
        )
        
        await self.register_tool(
            name="write_file",
            description="Write contents to a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            },
            handler=self._handle_write_file
        )
        
        # Web scraping
        await self.register_tool(
            name="fetch_url",
            description="Fetch content from a URL",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "method": {"type": "string", "enum": ["GET", "POST"], "default": "GET"}
                },
                "required": ["url"]
            },
            handler=self._handle_fetch_url
        )
        
        # Database operations
        await self.register_tool(
            name="execute_query",
            description="Execute a database query",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute"},
                    "params": {"type": "object", "description": "Query parameters"}
                },
                "required": ["query"]
            },
            handler=self._handle_execute_query
        )
    
    async def _register_default_resources(self) -> None:
        """Register default MCP resources"""
        await self.register_resource(
            uri="file://system/logs",
            name="System Logs",
            description="Access to system log files",
            mime_type="text/plain"
        )
        
        await self.register_resource(
            uri="db://tenant-data",
            name="Tenant Database",
            description="Access to tenant-specific database",
            mime_type="application/json"
        )
    
    async def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Any
    ) -> None:
        """Register a new MCP tool"""
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler
        )
        self.tools[name] = tool
        logger.info("Registered MCP tool", tool_name=name)
    
    async def register_resource(
        self,
        uri: str,
        name: str,
        description: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> None:
        """Register a new MCP resource"""
        resource = MCPResource(
            uri=uri,
            name=name,
            description=description,
            mime_type=mime_type
        )
        self.resources[uri] = resource
        logger.info("Registered MCP resource", resource_uri=uri, resource_name=name)
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call an MCP tool"""
        if not self.enabled:
            raise ValueError("MCP is disabled")
        
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        
        tool = self.tools[name]
        
        try:
            logger.info("Calling MCP tool", tool_name=name, tenant_id=tenant_id)
            
            # Validate arguments against schema
            self._validate_arguments(arguments, tool.input_schema)
            
            # Call the tool handler with tenant context
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(arguments, tenant_id=tenant_id)
            else:
                result = tool.handler(arguments, tenant_id=tenant_id)
            
            logger.info("MCP tool completed", tool_name=name, tenant_id=tenant_id)
            return {"success": True, "result": result}
            
        except Exception as e:
            logger.error("MCP tool error", tool_name=name, error=str(e), tenant_id=tenant_id)
            return {"success": False, "error": str(e)}
    
    async def get_resource(self, uri: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get an MCP resource"""
        if not self.enabled:
            raise ValueError("MCP is disabled")
        
        if uri not in self.resources:
            raise ValueError(f"Resource '{uri}' not found")
        
        resource = self.resources[uri]
        
        try:
            logger.info("Getting MCP resource", resource_uri=uri, tenant_id=tenant_id)
            
            # Handle different resource types
            if uri.startswith("file://"):
                content = await self._get_file_resource(uri, tenant_id)
            elif uri.startswith("db://"):
                content = await self._get_db_resource(uri, tenant_id)
            elif uri.startswith("http://") or uri.startswith("https://"):
                content = await self._get_web_resource(uri, tenant_id)
            else:
                raise ValueError(f"Unsupported resource URI scheme: {uri}")
            
            return {
                "success": True,
                "content": content,
                "resource": resource.__dict__
            }
            
        except Exception as e:
            logger.error("MCP resource error", resource_uri=uri, error=str(e), tenant_id=tenant_id)
            return {"success": False, "error": str(e)}
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available MCP tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self.tools.values()
        ]
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """List all available MCP resources"""
        return [resource.__dict__ for resource in self.resources.values()]
    
    def _validate_arguments(self, arguments: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Validate arguments against JSON schema"""
        # Basic validation - in production, use jsonschema library
        if "required" in schema:
            for required_field in schema["required"]:
                if required_field not in arguments:
                    raise ValueError(f"Missing required argument: {required_field}")
    
    # Tool handlers
    async def _handle_read_file(self, arguments: Dict[str, Any], tenant_id: Optional[str] = None) -> str:
        """Handle read_file tool"""
        # In production, implement proper file access with tenant isolation
        return f"File content from {arguments['path']} (tenant: {tenant_id})"
    
    async def _handle_write_file(self, arguments: Dict[str, Any], tenant_id: Optional[str] = None) -> str:
        """Handle write_file tool"""
        # In production, implement proper file writing with tenant isolation
        return f"Written to {arguments['path']} (tenant: {tenant_id})"
    
    async def _handle_fetch_url(self, arguments: Dict[str, Any], tenant_id: Optional[str] = None) -> str:
        """Handle fetch_url tool"""
        # In production, implement proper HTTP client with rate limiting
        return f"Content from {arguments['url']} (tenant: {tenant_id})"
    
    async def _handle_execute_query(self, arguments: Dict[str, Any], tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle execute_query tool"""
        # In production, implement proper database query execution with tenant isolation
        return {"query": arguments["query"], "tenant_id": tenant_id, "results": []}
    
    # Resource handlers
    async def _get_file_resource(self, uri: str, tenant_id: Optional[str] = None) -> str:
        """Get file resource content"""
        # In production, implement proper file access
        return f"File resource content for {uri}"
    
    async def _get_db_resource(self, uri: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get database resource content"""
        # In production, implement proper database access
        return {"data": f"Database resource for {uri}", "tenant_id": tenant_id}
    
    async def _get_web_resource(self, uri: str, tenant_id: Optional[str] = None) -> str:
        """Get web resource content"""
        # In production, implement proper HTTP client
        return f"Web resource content for {uri}"