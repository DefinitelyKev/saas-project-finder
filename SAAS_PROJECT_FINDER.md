# SaaS Project Finder Agent System

## Overview

The SaaS Project Finder Agent System is a comprehensive AI-powered solution that automatically discovers, analyzes, and ranks trending SaaS project ideas from multiple platforms. It uses specialized AI agents with MCP (Model Context Protocol) integration to provide weekly curated reports of the best AI-agent-suitable projects.

## Features

### 🔍 Multi-Platform Discovery
- **ProductHunt**: Trending product launches and innovations
- **Reddit**: Startup communities (r/startups, r/entrepreneur, r/SaaS, etc.)
- **IndieHackers**: Bootstrapped project stories and revenue insights
- **Twitter/X**: Real-time startup discussions and trends

### 🤖 AI-Powered Analysis
- **Trend Momentum Scoring**: Social engagement and growth analysis
- **Market Potential Assessment**: Market size and opportunity evaluation
- **AI Suitability Rating**: How well ideas fit AI agent implementation
- **Competition Analysis**: Market saturation and differentiation opportunities
- **Implementation Feasibility**: Development complexity and time estimates
- **Monetization Potential**: Revenue model viability assessment

### 📊 Comprehensive Ranking System
- **Weighted Scoring Algorithm**: Customizable criteria weights
- **Real-time Rankings**: Daily updated leaderboards
- **Trend Tracking**: Week-over-week position changes
- **Historical Data**: Performance tracking over time

### 📧 Automated Reporting
- **Weekly Email Reports**: Top 10 ideas with detailed analysis
- **Market Insights**: Trending categories and emerging opportunities
- **Immediate Alerts**: High-potential ideas (score ≥85) notifications
- **HTML & Text Formats**: Professional email templates

### ⏰ Automated Scheduling
- **Daily Scanning** (9 AM UTC): Discovery of new ideas
- **Afternoon Analysis** (2 PM UTC): AI-powered evaluation
- **Evening Ranking** (6 PM UTC): Score updates and positioning
- **Weekly Reports** (Sunday 10 AM UTC): Comprehensive summaries

## Architecture

### AI Agents

#### 1. SaaS Trend Scanner Agent (`saas-trend-scanner`)
**Purpose**: Discovers trending SaaS ideas across multiple platforms

**Tools**:
- `search_producthunt`: ProductHunt trending products
- `search_reddit_startups`: Reddit startup discussions
- `search_indiehackers`: IndieHackers project stories
- `search_twitter_trends`: Twitter/X startup conversations
- `extract_idea_details`: Structure discovered content

**Output**: Raw idea data with engagement metrics

#### 2. SaaS Idea Analyzer Agent (`saas-idea-analyzer`)
**Purpose**: Evaluates ideas for market potential and feasibility

**Tools**:
- `analyze_market_size`: Research market opportunities
- `analyze_competition`: Competitive landscape analysis
- `check_domain_availability`: Domain name research
- `calculate_ai_suitability`: AI implementation assessment
- `estimate_development_time`: Implementation complexity

**Output**: Comprehensive analysis with individual scores

#### 3. SaaS Project Ranker Agent (`saas-project-ranker`)
**Purpose**: Ranks ideas using weighted scoring algorithms

**Tools**:
- `calculate_trend_score`: Momentum analysis
- `calculate_composite_score`: Final weighted scoring
- `analyze_google_trends`: Search interest validation
- `compare_with_competitors`: Competitive positioning

**Output**: Final rankings and recommendations

### Database Schema

#### Core Tables

**saas_project_ideas**
- Idea metadata (title, description, source)
- Scoring metrics (trend, market, AI suitability, etc.)
- Ranking data (position, changes)
- Analysis results and timestamps

**trending_metrics**
- Platform-specific engagement data
- Growth rates and sentiment analysis
- Time-series tracking

**weekly_reports**
- Generated report content
- Email delivery tracking
- Market insights summaries

**saas_idea_analysis_logs**
- Agent execution history
- Performance metrics
- Error tracking

### Scoring Algorithm

The composite score uses weighted criteria:

```
Composite Score = (
    Trend Score × 0.25 +           // Social momentum
    Market Score × 0.20 +          // Market potential
    AI Suitability × 0.20 +       // Implementation fit
    Competition Score × 0.15 +     // Market opportunity
    Feasibility Score × 0.10 +     // Development ease
    Monetization Score × 0.10      // Revenue potential
)
```

**Scoring Scale**: 0-100 (higher is better)
- **Excellent**: 80-100
- **Good**: 65-79
- **Average**: 50-64
- **Poor**: 0-49

## API Endpoints

### SaaS Ideas Management

```http
GET /api/v1/saas-ideas/
```
Paginated list with filtering and sorting

```http
GET /api/v1/saas-ideas/top?limit=10
```
Top-ranked ideas

```http
GET /api/v1/saas-ideas/trending?limit=10
```
Highest momentum ideas

```http
GET /api/v1/saas-ideas/{idea_id}
```
Detailed idea information

```http
GET /api/v1/saas-ideas/insights/market
```
Market trends and insights

### Reports & Analytics

```http
GET /api/v1/saas-ideas/reports/weekly
```
Historical weekly reports

```http
POST /api/v1/saas-ideas/reports/weekly/send
```
Trigger manual report generation

### Scheduler Management

```http
GET /api/v1/saas-ideas/scheduler/status
```
View scheduler and job status

```http
POST /api/v1/saas-ideas/scheduler/scan
```
Trigger manual platform scanning

```http
POST /api/v1/saas-ideas/scheduler/analyze
```
Trigger manual idea analysis

```http
POST /api/v1/saas-ideas/scheduler/ranking
```
Trigger manual ranking update

## Configuration

### Environment Variables

```bash
# MCP Configuration
MCP_SERVER_URL=http://localhost:8080
MCP_API_KEY=your_mcp_api_key

# Email Service
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM_ADDRESS=saas-finder@company.com
EMAIL_REPORT_RECIPIENTS=admin@company.com,team@company.com

# External APIs
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
PRODUCTHUNT_API_TOKEN=your_producthunt_token
GOOGLE_TRENDS_API_KEY=your_google_trends_key

# Scoring Weights (must sum to 1.0)
TREND_WEIGHT=0.25
MARKET_WEIGHT=0.20
AI_SUITABILITY_WEIGHT=0.20
COMPETITION_WEIGHT=0.15
FEASIBILITY_WEIGHT=0.10
MONETIZATION_WEIGHT=0.10

# Alert Thresholds
HIGH_POTENTIAL_SCORE_THRESHOLD=85.0
IMMEDIATE_ALERT_ENABLED=true
```

### Scheduler Configuration

The system runs automated tasks on the following schedule:

- **9 AM UTC**: Daily trend scanning across all platforms
- **2 PM UTC**: Analysis of newly discovered ideas
- **6 PM UTC**: Ranking updates and score calculations
- **Sunday 10 AM UTC**: Weekly report generation and email delivery
- **Every 4 hours**: Continuous ranking updates

## Setup Instructions

### 1. Environment Setup

```bash
# Copy environment configuration
cp .env.example .env

# Edit .env with your API keys and configuration
```

### 2. Database Migration

```bash
# Run database migrations
alembic upgrade head
```

### 3. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (for web scraping)
playwright install
```

### 4. Start Services

```bash
# Start database and Redis
docker-compose up -d postgres redis

# Start the application
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# Check scheduler status
curl -H "X-API-Key: your-tenant-api-key" \
     http://localhost:8000/api/v1/saas-ideas/scheduler/status
```

## Usage Examples

### Manual Operations

```bash
# Trigger manual scan
curl -X POST \
  -H "X-API-Key: your-tenant-api-key" \
  -H "Content-Type: application/json" \
  -d '{"platform": "producthunt"}' \
  http://localhost:8000/api/v1/saas-ideas/scheduler/scan

# Get top ideas
curl -H "X-API-Key: your-tenant-api-key" \
     http://localhost:8000/api/v1/saas-ideas/top?limit=5

# Send weekly report
curl -X POST \
  -H "X-API-Key: your-tenant-api-key" \
  http://localhost:8000/api/v1/saas-ideas/reports/weekly/send
```

### Weekly Report Example

The system generates professional HTML email reports including:

- **Executive Summary**: Week overview with key metrics
- **Top 10 Ideas**: Ranked list with detailed analysis
- **Market Insights**: Dominant trends and emerging opportunities
- **Implementation Notes**: AI suitability and development guidance
- **Source Attribution**: Platform and engagement metrics

## Monitoring & Maintenance

### Performance Metrics

- **Discovery Rate**: Ideas found per day (target: 20-50)
- **Analysis Success**: Percentage of successful evaluations (target: >95%)
- **Email Delivery**: Weekly report success rate (target: >90%)
- **Scoring Accuracy**: Manual validation of high-scoring ideas

### Troubleshooting

#### Common Issues

1. **MCP Tool Failures**: Check API keys and rate limits
2. **Email Delivery Issues**: Verify SMTP credentials and recipients
3. **Scheduler Not Running**: Check `SCHEDULER_ENABLED` environment variable
4. **Low Discovery Rate**: Validate platform API access

#### Logs and Debugging

```bash
# View application logs
docker-compose logs -f ai-backend

# Check scheduler job status
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/api/v1/saas-ideas/scheduler/status

# Database admin interface
open http://localhost:5050  # pgAdmin
```

## Success Metrics

### Expected Outcomes

- **20-50 new ideas discovered daily** across all platforms
- **Weekly ranking of 100+ active ideas** with comprehensive analysis
- **90%+ email delivery rate** for weekly reports
- **<5% false positive rate** for trend detection
- **85+ average score accuracy** for high-potential ideas

### Value Proposition

This system enables users to:

1. **Stay ahead of trends** with automated discovery
2. **Make data-driven decisions** with comprehensive scoring
3. **Focus on AI-suitable opportunities** with targeted filtering
4. **Save research time** with automated analysis
5. **Identify market gaps** with competitive intelligence

## Contributing

The SaaS Project Finder system is designed to be extensible:

- **Add new platforms** by extending MCP tools
- **Customize scoring weights** via environment variables
- **Implement new analysis criteria** in the ranking service
- **Enhance email templates** with additional insights
- **Add new alert types** for specific opportunity patterns

For questions or contributions, refer to the main project documentation and development guidelines.