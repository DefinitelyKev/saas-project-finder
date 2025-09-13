from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.config.constants import AgentType


@dataclass
class AgentTool:
    """Represents a tool available to an agent."""

    type: str  # "function", "mcp"
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    server: Optional[str] = None  # For MCP tools
    capabilities: List[str] = field(default_factory=list)  # For MCP tools


@dataclass
class Agent:
    """Agent entity representing a pre-configured AI agent."""

    id: str
    name: str
    description: str
    model: str
    system_prompt: str
    tools: List[AgentTool] = field(default_factory=list)
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    max_tokens: int = 1000
    temperature: float = 0.7
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Usage tracking
    total_executions: int = 0
    total_tokens_used: int = 0
    success_rate: float = 0.0

    def get_tool_by_name(self, tool_name: str) -> Optional[AgentTool]:
        """Get tool by name."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None

    def get_mcp_tools(self) -> List[AgentTool]:
        """Get all MCP tools."""
        return [tool for tool in self.tools if tool.type == "mcp"]

    def get_function_tools(self) -> List[AgentTool]:
        """Get all function tools."""
        return [tool for tool in self.tools if tool.type == "function"]

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters against schema."""
        # Basic validation - in production would use jsonschema
        required = self.parameters_schema.get("required", [])
        properties = self.parameters_schema.get("properties", {})

        # Check required parameters
        for param in required:
            if param not in parameters:
                return False

        # Check parameter types
        for param, value in parameters.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if expected_type and not self._validate_type(value, expected_type):
                    return False

        return True

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        if expected_type in type_map:
            return isinstance(value, type_map[expected_type])
        return True

    def update_usage_stats(self, tokens_used: int, success: bool) -> None:
        """Update usage statistics."""
        self.total_executions += 1
        self.total_tokens_used += tokens_used

        if success:
            self.success_rate = (
                (self.success_rate * (self.total_executions - 1) + 1) / self.total_executions
            )
        else:
            self.success_rate = (
                self.success_rate * (self.total_executions - 1) / self.total_executions
            )