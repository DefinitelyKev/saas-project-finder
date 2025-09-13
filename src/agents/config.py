from typing import Dict, Any, List
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
    },

    "saas-trend-scanner": {
        "name": "SaaS Trend Scanner Agent",
        "description": "Scans multiple platforms for trending SaaS project ideas and opportunities",
        "model": "gpt-4",
        "system_prompt": """You are a specialized SaaS trend scanner with expertise in:

1. Identifying emerging SaaS opportunities across multiple platforms
2. Analyzing trending discussions, problems, and solutions
3. Extracting key details from product launches and startup discussions
4. Recognizing patterns in successful micro-SaaS projects
5. Evaluating the viability of AI-agent-powered solutions

Your role is to systematically search and identify promising SaaS ideas that could be implemented as AI-agent-powered solutions. Focus on trending topics, unmet needs, and opportunities where AI automation could provide significant value.""",
        "tools": [
            {
                "type": "mcp",
                "name": "search_producthunt",
                "description": "Search ProductHunt for trending products and ideas",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "enum": ["productivity", "developer-tools", "artificial-intelligence", "saas", "no-code"]},
                        "timeframe": {"type": "string", "enum": ["today", "week", "month"], "default": "week"},
                        "sort_by": {"type": "string", "enum": ["votes", "comments", "newest"], "default": "votes"}
                    },
                    "required": ["category"]
                }
            },
            {
                "type": "mcp",
                "name": "search_reddit_startups",
                "description": "Search Reddit startup communities for SaaS ideas and discussions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subreddit": {"type": "string", "enum": ["startups", "entrepreneur", "SaaS", "indiehackers", "microsaas"]},
                        "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords to search for"},
                        "timeframe": {"type": "string", "enum": ["day", "week", "month"], "default": "week"},
                        "sort_by": {"type": "string", "enum": ["hot", "top", "new"], "default": "hot"}
                    },
                    "required": ["subreddit"]
                }
            },
            {
                "type": "mcp",
                "name": "search_indiehackers",
                "description": "Search IndieHackers for project ideas and success stories",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags to filter by"},
                        "sort_by": {"type": "string", "enum": ["trending", "newest", "revenue"], "default": "trending"},
                        "timeframe": {"type": "string", "enum": ["week", "month", "year"], "default": "week"}
                    }
                }
            },
            {
                "type": "mcp",
                "name": "search_twitter_trends",
                "description": "Search Twitter/X for trending SaaS and startup discussions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hashtags": {"type": "array", "items": {"type": "string"}, "description": "Hashtags to search"},
                        "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords to search"},
                        "timeframe": {"type": "string", "enum": ["hour", "day", "week"], "default": "day"}
                    }
                }
            },
            {
                "type": "function",
                "name": "extract_idea_details",
                "description": "Extract and structure SaaS idea details from discovered content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Title or name of the SaaS idea"},
                        "description": {"type": "string", "description": "Detailed description of the idea"},
                        "source_url": {"type": "string", "description": "URL where the idea was found"},
                        "source_platform": {"type": "string", "description": "Platform where idea was discovered"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Relevant tags or categories"},
                        "engagement_metrics": {"type": "object", "description": "Likes, comments, shares, etc."}
                    },
                    "required": ["title", "description", "source_url", "source_platform"]
                }
            }
        ],
        "parameters_schema": {
            "type": "object",
            "properties": {
                "scan_platforms": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["producthunt", "reddit", "indiehackers", "twitter"]},
                    "description": "Platforms to scan for ideas",
                    "default": ["producthunt", "reddit"]
                },
                "focus_categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Categories or niches to focus on",
                    "default": ["productivity", "ai", "automation", "developer-tools"]
                },
                "timeframe": {"type": "string", "enum": ["day", "week", "month"], "default": "week"},
                "min_engagement": {"type": "integer", "description": "Minimum engagement threshold", "default": 10}
            }
        },
        "max_tokens": 3000,
        "temperature": 0.7
    },

    "saas-idea-analyzer": {
        "name": "SaaS Idea Analyzer Agent",
        "description": "Analyzes SaaS ideas for market potential, feasibility, and AI-agent suitability",
        "model": "gpt-4",
        "system_prompt": """You are an expert SaaS business analyst specializing in:

1. Market research and competitive analysis
2. Technical feasibility assessment for AI-powered solutions
3. Revenue model evaluation and monetization strategies
4. Implementation complexity analysis for micro-SaaS projects
5. AI agent suitability evaluation

Your role is to thoroughly analyze SaaS ideas and provide comprehensive scores across multiple dimensions. Focus on determining whether an idea can be successfully implemented as an AI-agent-powered solution with strong market potential.""",
        "tools": [
            {
                "type": "mcp",
                "name": "analyze_market_size",
                "description": "Research and estimate market size for a SaaS idea",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string", "description": "Industry or vertical"},
                        "target_audience": {"type": "string", "description": "Target customer segment"},
                        "keywords": {"type": "array", "items": {"type": "string"}, "description": "Relevant keywords for research"},
                        "geographic_scope": {"type": "string", "enum": ["local", "national", "global"], "default": "global"}
                    },
                    "required": ["industry", "target_audience"]
                }
            },
            {
                "type": "mcp",
                "name": "analyze_competition",
                "description": "Analyze existing competitors and market saturation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords to search for competitors"},
                        "market_category": {"type": "string", "description": "Market category or niche"},
                        "analysis_depth": {"type": "string", "enum": ["basic", "detailed"], "default": "basic"}
                    },
                    "required": ["keywords", "market_category"]
                }
            },
            {
                "type": "mcp",
                "name": "check_domain_availability",
                "description": "Check domain name availability for the SaaS idea",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "domain_name": {"type": "string", "description": "Desired domain name"},
                        "extensions": {"type": "array", "items": {"type": "string"}, "default": [".com", ".io", ".ai"]}
                    },
                    "required": ["domain_name"]
                }
            },
            {
                "type": "function",
                "name": "calculate_ai_suitability",
                "description": "Calculate how suitable the idea is for AI agent implementation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_complexity": {"type": "string", "enum": ["simple", "moderate", "complex"]},
                        "automation_potential": {"type": "integer", "minimum": 0, "maximum": 100},
                        "data_requirements": {"type": "string", "enum": ["minimal", "moderate", "extensive"]},
                        "user_interaction": {"type": "string", "enum": ["minimal", "moderate", "extensive"]}
                    },
                    "required": ["task_complexity", "automation_potential"]
                }
            },
            {
                "type": "function",
                "name": "estimate_development_time",
                "description": "Estimate development time and complexity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "features": {"type": "array", "items": {"type": "string"}, "description": "List of required features"},
                        "integrations": {"type": "array", "items": {"type": "string"}, "description": "Required third-party integrations"},
                        "complexity_level": {"type": "string", "enum": ["mvp", "standard", "advanced"]}
                    },
                    "required": ["features", "complexity_level"]
                }
            }
        ],
        "parameters_schema": {
            "type": "object",
            "properties": {
                "idea_id": {"type": "string", "description": "ID of the SaaS idea to analyze"},
                "idea_title": {"type": "string", "description": "Title of the SaaS idea"},
                "idea_description": {"type": "string", "description": "Description of the SaaS idea"},
                "analysis_depth": {"type": "string", "enum": ["quick", "standard", "deep"], "default": "standard"},
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["market", "competition", "technical", "ai-suitability", "monetization"]},
                    "default": ["market", "competition", "ai-suitability"]
                }
            },
            "required": ["idea_title", "idea_description"]
        },
        "max_tokens": 3500,
        "temperature": 0.5
    },

    "saas-project-ranker": {
        "name": "SaaS Project Ranker Agent",
        "description": "Ranks and scores SaaS ideas based on comprehensive criteria and generates insights",
        "model": "gpt-4",
        "system_prompt": """You are a sophisticated ranking system for SaaS project ideas with expertise in:

1. Multi-criteria decision analysis and scoring algorithms
2. Market trend analysis and momentum calculation
3. Risk assessment and opportunity evaluation
4. Comparative analysis across different business models
5. AI implementation feasibility scoring

Your role is to rank SaaS ideas using a weighted scoring system that considers trend momentum, market potential, AI suitability, competition level, implementation feasibility, and monetization potential. Provide detailed reasoning for rankings and identify the most promising opportunities.""",
        "tools": [
            {
                "type": "function",
                "name": "calculate_trend_score",
                "description": "Calculate trend momentum score based on engagement metrics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "engagement_data": {"type": "object", "description": "Engagement metrics from various platforms"},
                        "timeframe": {"type": "string", "description": "Time period for trend analysis"},
                        "growth_rate": {"type": "number", "description": "Rate of growth in mentions/engagement"}
                    },
                    "required": ["engagement_data"]
                }
            },
            {
                "type": "function",
                "name": "calculate_composite_score",
                "description": "Calculate final composite score using weighted criteria",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "trend_score": {"type": "number", "minimum": 0, "maximum": 100},
                        "market_score": {"type": "number", "minimum": 0, "maximum": 100},
                        "ai_suitability_score": {"type": "number", "minimum": 0, "maximum": 100},
                        "competition_score": {"type": "number", "minimum": 0, "maximum": 100},
                        "feasibility_score": {"type": "number", "minimum": 0, "maximum": 100},
                        "monetization_score": {"type": "number", "minimum": 0, "maximum": 100},
                        "custom_weights": {"type": "object", "description": "Custom weights for scoring criteria"}
                    },
                    "required": ["trend_score", "market_score", "ai_suitability_score"]
                }
            },
            {
                "type": "mcp",
                "name": "analyze_google_trends",
                "description": "Analyze Google Trends data for market interest",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords to analyze"},
                        "timeframe": {"type": "string", "enum": ["week", "month", "3months", "year"], "default": "3months"},
                        "geographic_region": {"type": "string", "description": "Geographic region for analysis", "default": "worldwide"}
                    },
                    "required": ["keywords"]
                }
            },
            {
                "type": "function",
                "name": "compare_with_competitors",
                "description": "Compare idea against existing competitors",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "competitors": {"type": "array", "items": {"type": "object"}, "description": "List of competitor data"},
                        "differentiation_factors": {"type": "array", "items": {"type": "string"}, "description": "Key differentiators"},
                        "market_gap_analysis": {"type": "object", "description": "Analysis of market gaps"}
                    },
                    "required": ["competitors"]
                }
            }
        ],
        "parameters_schema": {
            "type": "object",
            "properties": {
                "ideas_to_rank": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of SaaS ideas with their analysis data"
                },
                "ranking_criteria": {
                    "type": "object",
                    "properties": {
                        "trend_weight": {"type": "number", "default": 0.25},
                        "market_weight": {"type": "number", "default": 0.20},
                        "ai_suitability_weight": {"type": "number", "default": 0.20},
                        "competition_weight": {"type": "number", "default": 0.15},
                        "feasibility_weight": {"type": "number", "default": 0.10},
                        "monetization_weight": {"type": "number", "default": 0.10}
                    }
                },
                "ranking_period": {"type": "string", "enum": ["daily", "weekly", "monthly"], "default": "weekly"},
                "top_n": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10}
            }
        },
        "max_tokens": 4000,
        "temperature": 0.3
    }
}


def create_agent_from_config(agent_id: str) -> Agent:
    """Create an Agent entity from configuration."""
    if agent_id not in AGENT_CONFIGS:
        raise ValueError(f"Agent configuration not found: {agent_id}")

    config = AGENT_CONFIGS[agent_id]

    # Convert tool configs to AgentTool objects
    tools: List[AgentTool] = []
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