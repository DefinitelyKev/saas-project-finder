# Agents Module

This directory contains the pre-configured AI agent definitions and tool configurations. All agent logic is centralized here, making the backend the single source of truth for agent capabilities.

## Structure

```
agents/
├── config.py          # All agent configurations and factory functions
└── tools/             # Custom tool implementations (future expansion)
```

## Agent Configuration System

### `config.py` - Agent Definitions
**Purpose**: Central registry for all AI agents with complete configurations.

**Key Components**:
- `AGENT_CONFIGS`: Dictionary mapping agent IDs to configurations
- `create_agent_from_config()`: Factory function to create Agent entities
- `get_all_agent_configs()`: Retrieve all available configurations
- `get_agent_ids()`: List of all available agent identifiers

## Pre-configured Agents

### Customer Support Agent (`customer-support`)
**Purpose**: Analyzes customer inquiries, provides solutions, and handles escalations.

**Configuration**:
- **Model**: GPT-4 for complex reasoning
- **Temperature**: 0.7 for balanced creativity and consistency
- **Max Tokens**: 1500 for comprehensive responses
- **Tools**: Knowledge base search, human escalation

**System Prompt Strategy**:
```
You are a professional customer support specialist. Your role is to:
1. Analyze customer inquiries and categorize them appropriately
2. Provide helpful, accurate solutions based on knowledge base
3. Maintain a friendly, professional tone
4. Escalate complex issues to human agents when necessary
5. Track customer satisfaction and follow up appropriately
```

**Parameters Schema**:
- `customer_message` (required): The customer's inquiry or issue
- `customer_tier` (optional): Customer's subscription level (free/pro/enterprise)
- `previous_context` (optional): Previous conversation context

**Available Tools**:
- `search_knowledge_base(query, category)`: Search FAQ, troubleshooting, or policies
- `escalate_to_human(reason, priority)`: Create support ticket with priority level

**Best Use Cases**:
- Support ticket automation
- FAQ responses
- Initial customer triage
- Knowledge base integration

### Data Analyst Agent (`data-analyst`)
**Purpose**: Performs data analysis, generates insights, and creates visualizations.

**Configuration**:
- **Model**: GPT-4 for analytical reasoning
- **Temperature**: 0.5 for consistent analytical outputs
- **Max Tokens**: 2000 for detailed analysis reports
- **Tools**: SQL execution, visualization creation

**System Prompt Strategy**:
```
You are an expert data analyst. Your capabilities include:
1. Analyzing datasets to identify trends, patterns, and anomalies
2. Generating actionable business insights from data
3. Creating clear, informative visualizations
4. Providing statistical analysis and interpretation
5. Recommending data-driven decisions
```

**Parameters Schema**:
- `analysis_type` (required): Type of analysis (trend_analysis, comparison, correlation, forecasting)
- `data_source` (required): Data source identifier
- `time_range` (optional): Time range for analysis (e.g., '30d', '3m', '1y')
- `metrics` (optional): Array of metrics to analyze
- `filters` (optional): Additional filters to apply

**Available Tools**:
- `execute_sql_query(query, database)`: Run SQL queries against databases
- `create_visualization(chart_type, data, title)`: Generate charts and graphs

**Best Use Cases**:
- Business intelligence dashboards
- Report generation
- Trend analysis
- Performance metrics

### Content Writer Agent (`content-writer`)
**Purpose**: Creates SEO-optimized content for various marketing purposes.

**Configuration**:
- **Model**: GPT-4 for high-quality content generation
- **Temperature**: 0.8 for creative writing
- **Max Tokens**: 4000 for long-form content
- **Tools**: Keyword research, competitor analysis

**System Prompt Strategy**:
```
You are an expert SEO content writer. Your expertise includes:
1. Creating engaging, high-quality content optimized for search engines
2. Incorporating target keywords naturally into content
3. Writing for different content types (blogs, landing pages, product descriptions)
4. Following SEO best practices for structure and readability
5. Adapting tone and style for different audiences
```

**Parameters Schema**:
- `content_type` (required): Type of content (blog_post, landing_page, product_description, social_media)
- `topic` (required): Main topic or subject
- `target_keywords` (optional): Array of keywords to target
- `word_count` (optional): Target word count (100-5000)
- `tone` (optional): Writing tone (professional, casual, authoritative, friendly)
- `target_audience` (optional): Audience description

**Available Tools**:
- `keyword_research(topic, competition_level)`: Research relevant keywords
- `analyze_competitors(competitor_urls, analysis_focus)`: Analyze competitor content

**Best Use Cases**:
- Blog post creation
- Landing page copy
- Product descriptions
- Social media content

### Code Reviewer Agent (`code-reviewer`)
**Purpose**: Reviews code for quality, security, and best practices.

**Configuration**:
- **Model**: GPT-4 for code understanding
- **Temperature**: 0.6 for balanced analysis
- **Max Tokens**: 2500 for detailed reviews
- **Tools**: Static analysis, improvement suggestions

**System Prompt Strategy**:
```
You are an expert code reviewer with deep knowledge of:
1. Code quality and best practices across multiple languages
2. Security vulnerabilities and common attack vectors
3. Performance optimization techniques
4. Code maintainability and readability
5. Testing strategies and coverage
```

**Parameters Schema**:
- `code` (required): Code to review
- `language` (required): Programming language
- `review_focus` (optional): Areas to focus on (security, performance, maintainability, testing)
- `context` (optional): Additional context about the code

**Available Tools**:
- `static_analysis(code, language, analysis_type)`: Perform automated code analysis
- `suggest_improvements(issue_type, severity, code_snippet)`: Generate specific suggestions

**Best Use Cases**:
- Automated code review
- Security audits
- Code quality enforcement
- Developer education

## Agent Configuration Structure

### Configuration Schema
```python
{
    "agent-id": {
        "name": "Human-readable agent name",
        "description": "What this agent does and its capabilities",
        "model": "gpt-4",  # OpenAI model to use
        "system_prompt": "Detailed instructions for agent behavior",
        "tools": [
            {
                "type": "function",  # or "mcp"
                "name": "tool_name",
                "description": "What this tool does",
                "parameters": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        ],
        "parameters_schema": {
            "type": "object",
            "properties": {
                "param_name": {
                    "type": "string",
                    "description": "Parameter description"
                }
            },
            "required": ["required_param"]
        },
        "max_tokens": 1000,
        "temperature": 0.7
    }
}
```

### Tool Types

#### Function Tools
Built-in Python functions registered in `ToolExecutor`:
- Direct function calls within the application
- Immediate execution and response
- Full control over implementation

#### MCP Tools (Future)
Model Context Protocol integrations:
- External service integrations
- Standardized tool interface
- Discoverable capabilities

## Adding New Agents

### Step-by-Step Process

1. **Define Configuration**
```python
"new-agent": {
    "name": "New Agent Name",
    "description": "Agent purpose and capabilities",
    "model": "gpt-4",
    "system_prompt": "Detailed behavior instructions...",
    "tools": [...],
    "parameters_schema": {...},
    "max_tokens": 1500,
    "temperature": 0.7
}
```

2. **Implement Required Tools**
Add tool functions to `src/infrastructure/ai/tool_executor.py`:
```python
async def _new_tool_function(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
    # Implementation
    return {"result": "tool output"}
```

3. **Register Tool in Executor**
```python
self.function_tools = {
    # existing tools...
    "new_tool_name": self._new_tool_function,
}
```

4. **Test Agent**
```cmd
# Create test tenant with access to new agent
python scripts/create_tenant.py

# Test agent execution
curl -X POST http://localhost:8000/api/v1/agents/new-agent/execute -H "X-API-Key: your-api-key" -H "Content-Type: application/json" -d "{\"parameters\": {\"test_param\": \"value\"}}"
```

5. **Update Documentation**
- Add agent description to README.md
- Update API documentation
- Add usage examples

## Agent Design Principles

### Prompt Engineering
- **Clear Role Definition**: Establish the agent's professional identity
- **Specific Instructions**: Detail expected behaviors and outputs
- **Context Setting**: Provide domain knowledge and constraints
- **Output Format**: Specify desired response structure

### Parameter Design
- **Required vs Optional**: Minimize required parameters for ease of use
- **Validation**: Use JSON schema for robust parameter validation
- **Flexibility**: Support various input formats and edge cases
- **Documentation**: Clear descriptions for all parameters

### Tool Integration
- **Single Responsibility**: Each tool should have one clear purpose
- **Error Handling**: Graceful failure with meaningful error messages
- **Parameter Validation**: Validate tool inputs before execution
- **Response Format**: Consistent return structure across all tools

### Performance Optimization
- **Token Efficiency**: Optimize prompts for minimal token usage
- **Caching**: Cache expensive tool results when appropriate
- **Streaming**: Support streaming for long responses
- **Timeouts**: Set appropriate limits for tool execution

## Security Considerations

### Input Validation
- All agent parameters validated against JSON schema
- Tool parameters sanitized before execution
- No direct code execution from user input
- SQL injection prevention in database tools

### Output Sanitization
- No sensitive information in agent responses
- PII detection and masking (future feature)
- Content filtering for inappropriate outputs
- Audit logging for compliance

### Access Control
- Tenant-based agent access restrictions
- Tool permission management
- Rate limiting per agent type
- Usage monitoring and alerting

## Monitoring and Analytics

### Agent Performance Metrics
- Execution success/failure rates
- Average response times
- Token usage patterns
- User satisfaction scores

### Usage Analytics
- Most popular agents per tenant
- Peak usage times and patterns
- Error frequency and types
- Cost optimization opportunities

### Tool Usage Tracking
- Tool invocation frequency
- Tool success/failure rates
- Performance bottlenecks
- Integration health monitoring

## Integration with Application

### Entity Creation
```python
from src.agents.config import create_agent_from_config

agent = create_agent_from_config("customer-support")
# Agent entity ready for execution
```

### Validation Flow
```python
# Parameter validation
if not agent.validate_parameters(user_params):
    raise InvalidAgentParameters(f"Invalid parameters for {agent.id}")

# Tool availability check
required_tools = agent.get_function_tools()
for tool in required_tools:
    if not tool_executor.has_tool(tool.name):
        raise AgentExecutionError(f"Tool {tool.name} not available")
```

### Execution Integration
The agent configurations integrate seamlessly with the execution pipeline:
1. FastAPI route validates agent exists
2. AgentExecutor loads configuration
3. OpenAI client uses agent settings
4. Tools are executed as needed
5. Results are formatted and returned

This centralized configuration approach ensures consistency across all agent operations while maintaining flexibility for customization and expansion.