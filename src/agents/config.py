from typing import Dict, Any
from src.domain.entities.agent import Agent, AgentTool

# Agent configurations - These are the pre-configured agents in the backend
AGENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "customer-support": {
        "name": "Customer Support Agent",
        "description": "Analyzes customer inquiries, provides solutions, and handles escalations",
        "model": "gpt-4",
        "system_prompt": """You are a professional customer support specialist. Your role is to:

1. Analyze customer inquiries and categorize them appropriately
2. Provide helpful, accurate solutions based on knowledge base
3. Maintain a friendly, professional tone
4. Escalate complex issues to human agents when necessary
5. Track customer satisfaction and follow up appropriately

Always be empathetic, solution-oriented, and thorough in your responses.""",
        "tools": [
            {
                "type": "function",
                "name": "search_knowledge_base",
                "description": "Search the company knowledge base for relevant information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "category": {"type": "string", "enum": ["faq", "troubleshooting", "policies"]}
                    },
                    "required": ["query"]
                }
            },
            {
                "type": "function",
                "name": "escalate_to_human",
                "description": "Escalate complex issues to human support agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {"type": "string", "description": "Reason for escalation"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}
                    },
                    "required": ["reason", "priority"]
                }
            }
        ],
        "parameters_schema": {
            "type": "object",
            "properties": {
                "customer_message": {"type": "string", "description": "The customer's inquiry or issue"},
                "customer_tier": {"type": "string", "enum": ["free", "pro", "enterprise"], "default": "free"},
                "previous_context": {"type": "string", "description": "Previous conversation context (optional)"}
            },
            "required": ["customer_message"]
        },
        "max_tokens": 1500,
        "temperature": 0.7
    },

    "data-analyst": {
        "name": "Data Analysis Agent",
        "description": "Performs data analysis, generates insights, and creates visualizations",
        "model": "gpt-4",
        "system_prompt": """You are an expert data analyst. Your capabilities include:

1. Analyzing datasets to identify trends, patterns, and anomalies
2. Generating actionable business insights from data
3. Creating clear, informative visualizations
4. Providing statistical analysis and interpretation
5. Recommending data-driven decisions

Always provide clear explanations of your methodology and confidence levels in your analysis.""",
        "tools": [
            {
                "type": "function",
                "name": "execute_sql_query",
                "description": "Execute SQL queries against the database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query to execute"},
                        "database": {"type": "string", "description": "Target database name"}
                    },
                    "required": ["query"]
                }
            },
            {
                "type": "function",
                "name": "create_visualization",
                "description": "Create charts and visualizations from data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "chart_type": {"type": "string", "enum": ["line", "bar", "pie", "scatter", "heatmap"]},
                        "data": {"type": "array", "description": "Data points for visualization"},
                        "title": {"type": "string", "description": "Chart title"}
                    },
                    "required": ["chart_type", "data", "title"]
                }
            }
        ],
        "parameters_schema": {
            "type": "object",
            "properties": {
                "analysis_type": {"type": "string", "enum": ["trend_analysis", "comparison", "correlation", "forecasting"]},
                "data_source": {"type": "string", "description": "Data source identifier"},
                "time_range": {"type": "string", "description": "Time range for analysis (e.g., '30d', '3m', '1y')"},
                "metrics": {"type": "array", "items": {"type": "string"}, "description": "Metrics to analyze"},
                "filters": {"type": "object", "description": "Additional filters to apply"}
            },
            "required": ["analysis_type", "data_source"]
        },
        "max_tokens": 2000,
        "temperature": 0.5
    },

    "content-writer": {
        "name": "SEO Content Writer",
        "description": "Creates SEO-optimized content for various marketing purposes",
        "model": "gpt-4",
        "system_prompt": """You are an expert SEO content writer. Your expertise includes:

1. Creating engaging, high-quality content optimized for search engines
2. Incorporating target keywords naturally into content
3. Writing for different content types (blogs, landing pages, product descriptions)
4. Following SEO best practices for structure and readability
5. Adapting tone and style for different audiences

Always prioritize value for readers while maintaining SEO optimization.""",
        "tools": [
            {
                "type": "function",
                "name": "keyword_research",
                "description": "Research relevant keywords for content optimization",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Main topic for keyword research"},
                        "competition_level": {"type": "string", "enum": ["low", "medium", "high"]}
                    },
                    "required": ["topic"]
                }
            },
            {
                "type": "function",
                "name": "analyze_competitors",
                "description": "Analyze competitor content for insights",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "competitor_urls": {"type": "array", "items": {"type": "string"}},
                        "analysis_focus": {"type": "string", "enum": ["keywords", "structure", "topics"]}
                    },
                    "required": ["competitor_urls"]
                }
            }
        ],
        "parameters_schema": {
            "type": "object",
            "properties": {
                "content_type": {"type": "string", "enum": ["blog_post", "landing_page", "product_description", "social_media"]},
                "topic": {"type": "string", "description": "Main topic or subject"},
                "target_keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords to target"},
                "word_count": {"type": "integer", "minimum": 100, "maximum": 5000, "description": "Target word count"},
                "tone": {"type": "string", "enum": ["professional", "casual", "authoritative", "friendly"], "default": "professional"},
                "target_audience": {"type": "string", "description": "Target audience description"}
            },
            "required": ["content_type", "topic"]
        },
        "max_tokens": 4000,
        "temperature": 0.8
    },

    "code-reviewer": {
        "name": "Code Review Agent",
        "description": "Reviews code for quality, security, and best practices",
        "model": "gpt-4",
        "system_prompt": """You are an expert code reviewer with deep knowledge of:

1. Code quality and best practices across multiple languages
2. Security vulnerabilities and common attack vectors
3. Performance optimization techniques
4. Code maintainability and readability
5. Testing strategies and coverage

Provide constructive feedback with specific suggestions for improvement.""",
        "tools": [
            {
                "type": "function",
                "name": "static_analysis",
                "description": "Perform static code analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to analyze"},
                        "language": {"type": "string", "description": "Programming language"},
                        "analysis_type": {"type": "string", "enum": ["security", "quality", "performance"]}
                    },
                    "required": ["code", "language"]
                }
            },
            {
                "type": "function",
                "name": "suggest_improvements",
                "description": "Generate specific improvement suggestions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "issue_type": {"type": "string", "description": "Type of issue found"},
                        "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                        "code_snippet": {"type": "string", "description": "Problematic code snippet"}
                    },
                    "required": ["issue_type", "severity"]
                }
            }
        ],
        "parameters_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code to review"},
                "language": {"type": "string", "description": "Programming language"},
                "review_focus": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["security", "performance", "maintainability", "testing"]},
                    "description": "Areas to focus the review on"
                },
                "context": {"type": "string", "description": "Additional context about the code"}
            },
            "required": ["code", "language"]
        },
        "max_tokens": 2500,
        "temperature": 0.6
    }
}


def create_agent_from_config(agent_id: str) -> Agent:
    """Create an Agent entity from configuration."""
    if agent_id not in AGENT_CONFIGS:
        raise ValueError(f"Agent configuration not found: {agent_id}")

    config = AGENT_CONFIGS[agent_id]

    # Convert tool configs to AgentTool objects
    tools = []
    for tool_config in config.get("tools", []):
        tool = AgentTool(
            type=tool_config["type"],
            name=tool_config["name"],
            description=tool_config["description"],
            parameters=tool_config.get("parameters", {}),
            server=tool_config.get("server"),
            capabilities=tool_config.get("capabilities", [])
        )
        tools.append(tool)

    return Agent(
        id=agent_id,
        name=config["name"],
        description=config["description"],
        model=config["model"],
        system_prompt=config["system_prompt"],
        tools=tools,
        parameters_schema=config["parameters_schema"],
        max_tokens=config["max_tokens"],
        temperature=config["temperature"]
    )


def get_all_agent_configs() -> Dict[str, Dict[str, Any]]:
    """Get all agent configurations."""
    return AGENT_CONFIGS


def get_agent_ids() -> list[str]:
    """Get list of all available agent IDs."""
    return list(AGENT_CONFIGS.keys())