# SaaS Project Finder Agent System

AI-powered system that discovers, analyzes, and ranks trending SaaS project ideas from multiple platforms with weekly automated reports.

## Features

- **Multi-Platform Discovery** - ProductHunt, Reddit, Hacker News, Twitter
- **AI-Powered Analysis** - Market potential, AI suitability, competition analysis
- **Automated Ranking** - Weighted scoring with configurable criteria
- **Weekly Reports** - Email summaries of top opportunities
- **Scheduled Jobs** - Daily scanning, analysis, and ranking updates

## Agents

### 1. SaaS Trend Scanner (`saas-trend-scanner`)
Discovers trending SaaS ideas across platforms
- Tools: search_producthunt, search_reddit_startups, search_hackernews

### 2. SaaS Idea Analyzer (`saas-idea-analyzer`)
Evaluates market potential and feasibility
- Tools: analyze_market_size, analyze_competition, check_domain_availability

### 3. SaaS Project Ranker (`saas-project-ranker`)
Ranks ideas using weighted scoring
- Tools: calculate_trend_score, analyze_google_trends, compare_competitors

## Scoring Algorithm

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

**Scale**: 0-100 (80+ excellent, 65-79 good, 50-64 average, <50 poor)

## API Endpoints

```http
GET /api/v1/saas-ideas/top?limit=10          # Top-ranked ideas
GET /api/v1/saas-ideas/trending?limit=10     # Highest momentum
GET /api/v1/saas-ideas/{idea_id}             # Detailed analysis
GET /api/v1/saas-ideas/insights/market       # Market trends

POST /api/v1/saas-ideas/scheduler/scan       # Manual scan trigger
POST /api/v1/saas-ideas/reports/weekly/send  # Generate report
GET /api/v1/saas-ideas/scheduler/status      # Job status
```

## Automation Schedule

- **9 AM UTC**: Daily platform scanning
- **2 PM UTC**: Analysis of new ideas
- **6 PM UTC**: Ranking updates
- **Sunday 10 AM UTC**: Weekly email reports
- **Every 4 hours**: Continuous ranking updates

## Setup

```bash
# Environment setup
cp .env.example .env
# Edit .env with API keys

# Start services (includes MCP server)
docker-compose up --build

# Verify installation
curl http://localhost:8000/health
curl http://localhost:8080/health
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/saas-ideas/scheduler/status
```

## Environment Variables

**Required:**
- `MCP_SERVER_URL` - MCP server URL (default: http://localhost:8080)
- `MCP_API_KEY` - MCP authentication
- `PRODUCTHUNT_API_TOKEN` - ProductHunt API access

**Email Configuration:**
- `SMTP_SERVER` - Email server
- `EMAIL_USERNAME/PASSWORD` - SMTP credentials
- `EMAIL_REPORT_RECIPIENTS` - Report recipients

**Scoring Weights (must sum to 1.0):**
- `TREND_WEIGHT=0.25`
- `MARKET_WEIGHT=0.20`
- `AI_SUITABILITY_WEIGHT=0.20`
- `COMPETITION_WEIGHT=0.15`
- `FEASIBILITY_WEIGHT=0.10`
- `MONETIZATION_WEIGHT=0.10`

## Manual Operations

```bash
# Trigger scan
curl -X POST -H "X-API-Key: key" \
  http://localhost:8000/api/v1/saas-ideas/scheduler/scan

# Get top ideas
curl -H "X-API-Key: key" \
  http://localhost:8000/api/v1/saas-ideas/top?limit=5

# Send weekly report
curl -X POST -H "X-API-Key: key" \
  http://localhost:8000/api/v1/saas-ideas/reports/weekly/send
```

## Troubleshooting

**Common Issues:**
1. MCP Server Down: `docker-compose restart mcp-server`
2. API Failures: Check API tokens in .env
3. Email Issues: Verify SMTP credentials
4. Low Discovery: Validate platform API access

**Debugging:**
```bash
# Check MCP health
curl http://localhost:8080/health

# Test MCP tools
./venv-python tests/test_mcp_tools.py

# View logs
docker-compose logs -f ai-backend

# Database admin
http://localhost:5050 (admin@ai-backend.com / admin)
```

## Success Metrics

- **20-50 new ideas discovered daily**
- **100+ active ideas ranked weekly**
- **90%+ email delivery rate**
- **85+ average score accuracy** for high-potential ideas