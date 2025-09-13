from typing import Dict, Any
import json
import structlog

from src.domain.entities.agent import AgentTool
from src.domain.exceptions import AgentExecutionError
from src.infrastructure.ai.mcp_tools import MCPToolExecutor

logger = structlog.get_logger()


class ToolExecutor:
    """Handles execution of agent tools."""

    def __init__(self):
        # Initialize MCP tool executor
        self.mcp_executor = MCPToolExecutor()

        # Register built-in tools
        self.function_tools = {
            "search_knowledge_base": self._search_knowledge_base,
            "escalate_to_human": self._escalate_to_human,
            "execute_sql_query": self._execute_sql_query,
            "create_visualization": self._create_visualization,
            "keyword_research": self._keyword_research,
            "analyze_competitors": self._analyze_competitors,
            "static_analysis": self._static_analysis,
            "suggest_improvements": self._suggest_improvements,
            # SaaS Project Finder specific tools
            "extract_idea_details": self._extract_idea_details,
            "calculate_ai_suitability": self._calculate_ai_suitability,
            "estimate_development_time": self._estimate_development_time,
            "calculate_trend_score": self._calculate_trend_score,
            "calculate_composite_score": self._calculate_composite_score,
            "compare_with_competitors": self._compare_with_competitors,
        }

    async def execute_tool(self, tool: AgentTool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters."""

        if tool.type == "function":
            return await self._execute_function_tool(tool, parameters)
        elif tool.type == "mcp":
            return await self._execute_mcp_tool(tool, parameters)
        else:
            raise AgentExecutionError(f"Unknown tool type: {tool.type}")

    async def _execute_function_tool(self, tool: AgentTool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a built-in function tool."""

        if tool.name not in self.function_tools:
            raise AgentExecutionError(f"Function tool not found: {tool.name}")

        try:
            handler = self.function_tools[tool.name]
            return await handler(parameters)
        except Exception as e:
            logger.error("Function tool execution failed",
                        tool_name=tool.name,
                        error=str(e))
            raise AgentExecutionError(f"Tool execution failed: {str(e)}")

    async def _execute_mcp_tool(self, tool: AgentTool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool using the MCP executor."""
        try:
            return await self.mcp_executor.execute_mcp_tool(tool.name, parameters)
        except Exception as e:
            logger.error("MCP tool execution failed",
                        tool_name=tool.name,
                        error=str(e))
            raise AgentExecutionError(f"MCP tool execution failed: {str(e)}")

    # Built-in tool implementations (mock implementations for now)

    async def _search_knowledge_base(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base for relevant information."""
        query = parameters.get("query", "")
        category = parameters.get("category", "general")

        # Mock implementation
        mock_results = {
            "faq": [
                {"question": "How do I reset my password?", "answer": "Click 'Forgot Password' on login page"},
                {"question": "How do I contact support?", "answer": "Email support@company.com or use live chat"},
            ],
            "troubleshooting": [
                {"issue": "Login problems", "solution": "Clear browser cache and try again"},
                {"issue": "Payment failed", "solution": "Check card details and try again"},
            ],
            "policies": [
                {"policy": "Refund Policy", "details": "30-day money-back guarantee"},
                {"policy": "Privacy Policy", "details": "We protect your personal information"},
            ]
        }

        results = mock_results.get(category, [])
        relevant_results = [r for r in results if query.lower() in json.dumps(r).lower()]

        return {
            "results": relevant_results[:3],  # Top 3 results
            "total_found": len(relevant_results),
            "query": query,
            "category": category
        }

    async def _escalate_to_human(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate issue to human agent."""
        reason = parameters.get("reason", "")
        priority = parameters.get("priority", "medium")

        # Mock implementation
        ticket_id = f"TICKET-{hash(reason) % 10000:04d}"

        return {
            "ticket_id": ticket_id,
            "status": "escalated",
            "priority": priority,
            "reason": reason,
            "estimated_response_time": "2-4 hours" if priority in ["high", "urgent"] else "24 hours"
        }

    async def _execute_sql_query(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query against database."""
        query = parameters.get("query", "")
        database = parameters.get("database", "default")

        # Mock implementation
        if "SELECT" in query.upper():
            return {
                "results": [
                    {"id": 1, "name": "Product A", "sales": 1500},
                    {"id": 2, "name": "Product B", "sales": 1200},
                    {"id": 3, "name": "Product C", "sales": 900},
                ],
                "row_count": 3,
                "execution_time_ms": 45
            }
        else:
            return {
                "message": "Query executed successfully",
                "affected_rows": 1,
                "execution_time_ms": 20
            }

    async def _create_visualization(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create visualization from data."""
        chart_type = parameters.get("chart_type", "bar")
        data = parameters.get("data", [])
        title = parameters.get("title", "Chart")

        # Mock implementation
        return {
            "chart_url": f"https://charts.example.com/{hash(str(data)) % 10000}.png",
            "chart_type": chart_type,
            "title": title,
            "data_points": len(data),
            "created_at": "2024-01-01T12:00:00Z"
        }

    async def _keyword_research(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Research keywords for topic."""
        topic = parameters.get("topic", "")
        competition_level = parameters.get("competition_level", "medium")

        # Mock implementation
        keywords = [
            {"keyword": f"{topic} guide", "volume": 1200, "difficulty": "medium"},
            {"keyword": f"best {topic}", "volume": 800, "difficulty": "high"},
            {"keyword": f"{topic} tips", "volume": 600, "difficulty": "low"},
            {"keyword": f"how to {topic}", "volume": 900, "difficulty": "medium"},
        ]

        return {
            "keywords": keywords,
            "total_found": len(keywords),
            "topic": topic,
            "competition_level": competition_level
        }

    async def _analyze_competitors(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitor content."""
        competitor_urls = parameters.get("competitor_urls", [])
        analysis_focus = parameters.get("analysis_focus", "keywords")

        # Mock implementation
        return {
            "competitors_analyzed": len(competitor_urls),
            "common_keywords": ["marketing", "strategy", "growth", "business"],
            "content_gaps": ["advanced tutorials", "case studies", "industry insights"],
            "recommendations": [
                "Focus on long-tail keywords",
                "Create more in-depth content",
                "Add visual elements"
            ]
        }

    async def _static_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform static code analysis."""
        code = parameters.get("code", "")
        language = parameters.get("language", "python")
        analysis_type = parameters.get("analysis_type", "quality")

        # Mock implementation
        issues = []
        if "password" in code.lower():
            issues.append({
                "type": "security",
                "severity": "high",
                "message": "Potential hardcoded password detected",
                "line": 1
            })

        if len(code.split('\n')) > 50:
            issues.append({
                "type": "maintainability",
                "severity": "medium",
                "message": "Function is too long, consider breaking it down",
                "line": 1
            })

        return {
            "issues": issues,
            "language": language,
            "analysis_type": analysis_type,
            "lines_analyzed": len(code.split('\n'))
        }

    async def _suggest_improvements(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate improvement suggestions."""
        issue_type = parameters.get("issue_type", "")
        severity = parameters.get("severity", "medium")
        code_snippet = parameters.get("code_snippet", "")

        # Mock implementation
        suggestions = {
            "security": [
                "Use environment variables for sensitive data",
                "Implement input validation",
                "Add authentication checks"
            ],
            "performance": [
                "Add caching layer",
                "Optimize database queries",
                "Use async operations"
            ],
            "maintainability": [
                "Extract constants",
                "Add unit tests",
                "Improve documentation"
            ]
        }

        return {
            "suggestions": suggestions.get(issue_type, ["Add comments", "Follow coding standards"]),
            "issue_type": issue_type,
            "severity": severity,
            "priority": "high" if severity in ["high", "critical"] else "medium"
        }

    # SaaS Project Finder specific tool implementations

    async def _extract_idea_details(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure SaaS idea details from discovered content."""
        title = parameters.get("title", "")
        description = parameters.get("description", "")
        source_url = parameters.get("source_url", "")
        source_platform = parameters.get("source_platform", "")
        tags = parameters.get("tags", [])
        engagement_metrics = parameters.get("engagement_metrics", {})

        # Extract additional insights from the content
        extracted_features = []
        if "automation" in description.lower():
            extracted_features.append("automation")
        if "ai" in description.lower() or "artificial intelligence" in description.lower():
            extracted_features.append("ai-powered")
        if "dashboard" in description.lower():
            extracted_features.append("analytics-dashboard")
        if "api" in description.lower():
            extracted_features.append("api-integration")

        # Estimate initial complexity
        complexity = "medium"
        if len(extracted_features) > 3:
            complexity = "high"
        elif len(extracted_features) <= 1:
            complexity = "low"

        return {
            "structured_idea": {
                "title": title,
                "description": description,
                "source_url": source_url,
                "source_platform": source_platform,
                "tags": tags,
                "engagement_metrics": engagement_metrics,
                "extracted_features": extracted_features,
                "estimated_complexity": complexity
            },
            "extraction_confidence": 0.85,
            "processed_at": "2024-01-15T12:00:00Z"
        }

    async def _calculate_ai_suitability(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate how suitable the idea is for AI agent implementation."""
        task_complexity = parameters.get("task_complexity", "moderate")
        automation_potential = parameters.get("automation_potential", 50)
        data_requirements = parameters.get("data_requirements", "moderate")
        user_interaction = parameters.get("user_interaction", "moderate")

        # Calculate base score from automation potential
        base_score = automation_potential

        # Adjust for task complexity
        complexity_multiplier = {"simple": 1.2, "moderate": 1.0, "complex": 0.8}
        base_score *= complexity_multiplier.get(task_complexity, 1.0)

        # Adjust for data requirements
        data_multiplier = {"minimal": 1.1, "moderate": 1.0, "extensive": 0.9}
        base_score *= data_multiplier.get(data_requirements, 1.0)

        # Adjust for user interaction requirements
        interaction_multiplier = {"minimal": 1.2, "moderate": 1.0, "extensive": 0.7}
        base_score *= interaction_multiplier.get(user_interaction, 1.0)

        # Ensure score is within 0-100 range
        final_score = max(0, min(100, base_score))

        suitability_level = "high" if final_score >= 75 else "medium" if final_score >= 50 else "low"

        return {
            "ai_suitability_score": final_score,
            "suitability_level": suitability_level,
            "factors": {
                "task_complexity": task_complexity,
                "automation_potential": automation_potential,
                "data_requirements": data_requirements,
                "user_interaction": user_interaction
            },
            "recommendations": [
                "Focus on rule-based automation features",
                "Implement natural language processing",
                "Consider predictive analytics capabilities"
            ] if final_score >= 70 else [
                "Simplify the automation scope",
                "Focus on specific use cases",
                "Consider hybrid human-AI approach"
            ]
        }

    async def _estimate_development_time(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate development time and complexity."""
        features = parameters.get("features", [])
        integrations = parameters.get("integrations", [])
        complexity_level = parameters.get("complexity_level", "standard")

        # Base time estimates in weeks
        base_times = {"mvp": 4, "standard": 8, "advanced": 16}
        base_time = base_times.get(complexity_level, 8)

        # Add time for features (1-3 weeks each)
        feature_time = len(features) * 2

        # Add time for integrations (1-4 weeks each)
        integration_time = len(integrations) * 3

        total_weeks = base_time + feature_time + integration_time

        # Estimate costs (assuming $100/hour, 40 hours/week)
        estimated_cost = total_weeks * 40 * 100

        return {
            "estimated_development_weeks": total_weeks,
            "estimated_cost_usd": estimated_cost,
            "complexity_level": complexity_level,
            "breakdown": {
                "base_development": base_time,
                "features": feature_time,
                "integrations": integration_time
            },
            "team_size_recommendation": 2 if total_weeks <= 12 else 3,
            "risk_factors": [
                "Third-party API dependencies",
                "Scaling challenges",
                "User adoption uncertainty"
            ]
        }

    async def _calculate_trend_score(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate trend momentum score based on engagement metrics."""
        engagement_data = parameters.get("engagement_data", {})
        timeframe = parameters.get("timeframe", "week")
        growth_rate = parameters.get("growth_rate", 0.0)

        # Extract metrics from engagement data
        total_engagement = 0
        platform_count = 0

        for platform, metrics in engagement_data.items():
            if isinstance(metrics, dict):
                platform_engagement = (
                    metrics.get("likes", 0) +
                    metrics.get("shares", 0) +
                    metrics.get("comments", 0) * 2 +  # Comments weighted higher
                    metrics.get("votes", 0)
                )
                total_engagement += platform_engagement
                platform_count += 1

        # Calculate base trend score
        if platform_count > 0:
            avg_engagement = total_engagement / platform_count
            # Normalize to 0-100 scale
            base_score = min(100, avg_engagement / 10)
        else:
            base_score = 0

        # Apply growth rate multiplier
        growth_multiplier = 1 + (growth_rate / 100)
        trend_score = base_score * growth_multiplier

        # Ensure within bounds
        trend_score = max(0, min(100, trend_score))

        momentum = "rising" if growth_rate > 10 else "stable" if growth_rate > -5 else "declining"

        return {
            "trend_score": trend_score,
            "momentum": momentum,
            "growth_rate": growth_rate,
            "total_engagement": total_engagement,
            "platforms_analyzed": platform_count,
            "timeframe": timeframe
        }

    async def _calculate_composite_score(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final composite score using weighted criteria."""
        trend_score = parameters.get("trend_score", 0)
        market_score = parameters.get("market_score", 0)
        ai_suitability_score = parameters.get("ai_suitability_score", 0)
        competition_score = parameters.get("competition_score", 50)
        feasibility_score = parameters.get("feasibility_score", 50)
        monetization_score = parameters.get("monetization_score", 50)

        # Default weights
        default_weights = {
            "trend_weight": 0.25,
            "market_weight": 0.20,
            "ai_suitability_weight": 0.20,
            "competition_weight": 0.15,
            "feasibility_weight": 0.10,
            "monetization_weight": 0.10
        }

        custom_weights = parameters.get("custom_weights", {})
        weights = {**default_weights, **custom_weights}

        # Calculate weighted composite score
        composite_score = (
            trend_score * weights["trend_weight"] +
            market_score * weights["market_weight"] +
            ai_suitability_score * weights["ai_suitability_weight"] +
            competition_score * weights["competition_weight"] +
            feasibility_score * weights["feasibility_weight"] +
            monetization_score * weights["monetization_weight"]
        )

        # Determine overall rating
        if composite_score >= 80:
            rating = "excellent"
        elif composite_score >= 65:
            rating = "good"
        elif composite_score >= 50:
            rating = "average"
        else:
            rating = "poor"

        return {
            "composite_score": round(composite_score, 2),
            "rating": rating,
            "component_scores": {
                "trend": trend_score,
                "market": market_score,
                "ai_suitability": ai_suitability_score,
                "competition": competition_score,
                "feasibility": feasibility_score,
                "monetization": monetization_score
            },
            "weights_used": weights,
            "recommendations": [
                "High potential for AI agent implementation",
                "Consider rapid prototyping approach",
                "Focus on user acquisition strategy"
            ] if composite_score >= 70 else [
                "Needs improvement in key areas",
                "Consider pivot or refinement",
                "Validate market demand first"
            ]
        }

    async def _compare_with_competitors(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Compare idea against existing competitors."""
        competitors = parameters.get("competitors", [])
        differentiation_factors = parameters.get("differentiation_factors", [])
        market_gap_analysis = parameters.get("market_gap_analysis", {})

        # Analyze competitive landscape
        competitive_advantages = []
        competitive_risks = []

        if len(competitors) < 3:
            competitive_advantages.append("Low competition in market")
        elif len(competitors) > 10:
            competitive_risks.append("Highly saturated market")

        # Analyze differentiation potential
        differentiation_strength = "strong" if len(differentiation_factors) >= 3 else "moderate" if len(differentiation_factors) >= 1 else "weak"

        # Calculate competitive score (higher = better position vs competitors)
        base_score = 100 - min(80, len(competitors) * 5)  # Reduce score for more competitors

        if differentiation_factors:
            base_score += len(differentiation_factors) * 10

        competitive_score = max(0, min(100, base_score))

        return {
            "competitive_score": competitive_score,
            "competitor_count": len(competitors),
            "differentiation_strength": differentiation_strength,
            "competitive_advantages": competitive_advantages,
            "competitive_risks": competitive_risks,
            "market_position": "strong" if competitive_score >= 70 else "moderate" if competitive_score >= 50 else "weak",
            "strategic_recommendations": [
                "Focus on unique value proposition",
                "Target underserved market segments",
                "Leverage AI capabilities for differentiation"
            ] if competitive_score >= 60 else [
                "Find specific niche market",
                "Consider partnership strategies",
                "Validate unique positioning"
            ]
        }

    async def close(self):
        """Close resources."""
        if hasattr(self.mcp_executor, 'close'):
            await self.mcp_executor.close()