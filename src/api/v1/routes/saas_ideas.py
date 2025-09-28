from typing import List, Dict, Any, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from uuid import UUID
import asyncio

from src.api.v1.dependencies import get_current_tenant, get_db_session
from src.services.ranking_service import SaaSIdeaRankingService
from src.services.email_service import EmailNotificationService
from src.services.scheduler import SaaSProjectFinderScheduler
from src.infrastructure.persistence.models import SaaSProjectIdeaModel, WeeklyReportModel
from src.infrastructure.persistence.database import get_async_session_factory
from src.domain.entities.tenant import Tenant
from sqlalchemy import select, desc, func
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/saas-ideas", tags=["SaaS Ideas"])


# Pydantic models for request/response
class SaaSIdeaResponse(BaseModel):
    id: str
    title: str
    description: str
    source_url: str
    source_platform: str
    composite_score: float
    ranking_position: Optional[int]
    rank_change: int
    scores: Dict[str, float]
    tags: List[str]
    estimated_market_size: Optional[str]
    implementation_difficulty: str
    discovered_at: str
    last_analyzed_at: Optional[str]

    class Config:
        from_attributes = True


class SaaSIdeaListResponse(BaseModel):
    ideas: List[SaaSIdeaResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool


class MarketInsightsResponse(BaseModel):
    dominant_trends: List[str]
    emerging_opportunities: List[Dict[str, Any]]
    ai_adoption_patterns: List[str]
    market_gaps: List[str]
    trending_categories: List[str]
    total_ideas_analyzed: int


class WeeklyReportResponse(BaseModel):
    id: str
    week_start: str
    week_end: str
    top_ideas: List[Dict[str, Any]]
    market_insights: MarketInsightsResponse
    total_ideas_analyzed: int
    new_ideas_discovered: int
    sent_at: Optional[str]
    delivery_status: str


class SchedulerStatusResponse(BaseModel):
    scheduler_running: bool
    jobs: Dict[str, Any]
    total_jobs: int


class ManualTriggerRequest(BaseModel):
    platform: Optional[str] = Field(None, description="Specific platform to scan (optional)")


# Initialize scheduler (will be done in main app)
scheduler = None


@router.get("/", response_model=SaaSIdeaListResponse)
async def get_saas_ideas(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("composite_score", description="Sort field"),
    order: str = Query("desc", description="Sort order (asc/desc)"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum composite score"),
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get paginated list of SaaS ideas with filtering and sorting."""

    try:
        ranking_service = SaaSIdeaRankingService(db)

        # Build query
        query = select(SaaSProjectIdeaModel).where(SaaSProjectIdeaModel.is_active == True)

        # Apply filters
        if platform:
            query = query.where(SaaSProjectIdeaModel.source_platform == platform)
        if min_score is not None:
            query = query.where(SaaSProjectIdeaModel.composite_score >= min_score)

        # Apply sorting
        sort_field = getattr(SaaSProjectIdeaModel, sort_by, SaaSProjectIdeaModel.composite_score)
        if order.lower() == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        ideas = result.scalars().all()

        # Format response
        idea_responses = []
        for idea in ideas:
            idea_responses.append(SaaSIdeaResponse(
                id=str(idea.id),
                title=idea.title,
                description=idea.description,
                source_url=idea.source_url,
                source_platform=idea.source_platform,
                composite_score=idea.composite_score,
                ranking_position=idea.current_ranking_position,
                rank_change=idea.weekly_rank_change,
                scores={
                    "trend": idea.trend_score,
                    "market": idea.market_potential_score,
                    "ai_suitability": idea.ai_agent_suitability_score,
                    "competition": idea.competition_score,
                    "monetization": idea.monetization_potential_score
                },
                tags=idea.tags,
                estimated_market_size=idea.estimated_market_size,
                implementation_difficulty=idea.implementation_difficulty,
                discovered_at=idea.discovered_at.isoformat(),
                last_analyzed_at=idea.last_analyzed_at.isoformat() if idea.last_analyzed_at else None
            ))

        has_next = total_count is not None and (offset + page_size) < total_count

        return SaaSIdeaListResponse(
            ideas=idea_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next
        )

    except Exception as e:
        logger.error("Failed to get SaaS ideas", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve SaaS ideas: {str(e)}")


@router.get("/top", response_model=List[SaaSIdeaResponse])
async def get_top_ideas(
    limit: int = Query(10, ge=1, le=50, description="Number of top ideas to return"),
    timeframe_days: Optional[int] = Query(None, ge=1, description="Filter by days since discovery"),
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get top-ranked SaaS ideas."""

    try:
        ranking_service = SaaSIdeaRankingService(db)
        top_ideas = await ranking_service.get_top_ideas(limit=limit, timeframe_days=timeframe_days)

        return [
            SaaSIdeaResponse(
                id=idea["id"],
                title=idea["title"],
                description=idea["description"],
                source_url=idea["source_url"],
                source_platform=idea["source_platform"],
                composite_score=idea["composite_score"],
                ranking_position=idea["ranking_position"],
                rank_change=0,  # Not available in this context
                scores=idea["scores"],
                tags=idea["tags"],
                estimated_market_size=idea["estimated_market_size"],
                implementation_difficulty=idea["implementation_difficulty"],
                discovered_at=idea["discovered_at"],
                last_analyzed_at=None
            )
            for idea in top_ideas
        ]

    except Exception as e:
        logger.error("Failed to get top SaaS ideas", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve top ideas: {str(e)}")


@router.get("/trending", response_model=List[Dict[str, Any]])
async def get_trending_ideas(
    limit: int = Query(10, ge=1, le=50, description="Number of trending ideas to return"),
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get trending SaaS ideas with highest momentum."""

    try:
        ranking_service = SaaSIdeaRankingService(db)
        trending_ideas = await ranking_service.get_trending_ideas(limit=limit)

        return trending_ideas

    except Exception as e:
        logger.error("Failed to get trending SaaS ideas", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trending ideas: {str(e)}")


@router.get("/{idea_id}", response_model=SaaSIdeaResponse)
async def get_saas_idea(
    idea_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get detailed information about a specific SaaS idea."""

    try:
        query = select(SaaSProjectIdeaModel).where(SaaSProjectIdeaModel.id == idea_id)
        result = await db.execute(query)
        idea = result.scalar_one_or_none()

        if not idea:
            raise HTTPException(status_code=404, detail="SaaS idea not found")

        return SaaSIdeaResponse(
            id=str(idea.id),
            title=idea.title,
            description=idea.description,
            source_url=idea.source_url,
            source_platform=idea.source_platform,
            composite_score=idea.composite_score,
            ranking_position=idea.current_ranking_position,
            rank_change=idea.weekly_rank_change,
            scores={
                "trend": idea.trend_score,
                "market": idea.market_potential_score,
                "ai_suitability": idea.ai_agent_suitability_score,
                "competition": idea.competition_score,
                "monetization": idea.monetization_potential_score
            },
            tags=idea.tags,
            estimated_market_size=idea.estimated_market_size,
            implementation_difficulty=idea.implementation_difficulty,
            discovered_at=idea.discovered_at.isoformat(),
            last_analyzed_at=idea.last_analyzed_at.isoformat() if idea.last_analyzed_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get SaaS idea", idea_id=str(idea_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve SaaS idea: {str(e)}")


@router.get("/insights/market")
async def get_market_insights(
    timeframe_days: int = Query(30, ge=1, description="Days to analyze"),
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get market insights and trends analysis."""

    try:
        ranking_service = SaaSIdeaRankingService(db)

        # Get recent top ideas for analysis
        top_ideas = await ranking_service.get_top_ideas(limit=50, timeframe_days=timeframe_days)

        # Analyze trends and patterns
        category_counts = {}
        platform_counts = {}
        avg_scores: Dict[str, float] = {
            "trend": 0.0,
            "market": 0.0,
            "ai_suitability": 0.0,
            "competition": 0.0,
            "monetization": 0.0
        }

        for idea in top_ideas:
            # Count categories
            for tag in idea.get("tags", []):
                category_counts[tag] = category_counts.get(tag, 0) + 1

            # Count platforms
            platform = idea.get("source_platform", "unknown")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

            # Accumulate scores
            scores = idea.get("scores", {})
            for key in avg_scores:
                avg_scores[key] += scores.get(key, 0)

        # Calculate averages
        if top_ideas:
            for key in avg_scores:
                avg_scores[key] = avg_scores[key] / len(top_ideas)

        # Generate insights
        dominant_trends = []
        if avg_scores["ai_suitability"] > 70:
            dominant_trends.append("Strong trend toward AI-powered solutions")
        if avg_scores["trend"] > 75:
            dominant_trends.append("High social engagement and momentum")

        emerging_opportunities = []
        high_market_low_comp = [
            idea for idea in top_ideas
            if idea["scores"]["market"] > 70 and idea["scores"]["competition"] > 60
        ]
        if high_market_low_comp:
            emerging_opportunities.append({
                "opportunity": "High market potential with low competition",
                "count": len(high_market_low_comp),
                "examples": [idea["title"] for idea in high_market_low_comp[:3]]
            })

        trending_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return MarketInsightsResponse(
            dominant_trends=dominant_trends,
            emerging_opportunities=emerging_opportunities,
            ai_adoption_patterns=[f"Average AI suitability: {avg_scores['ai_suitability']:.1f}/100"],
            market_gaps=[idea["title"] for idea in top_ideas if idea["scores"]["competition"] > 80][:5],
            trending_categories=[cat[0] for cat in trending_categories],
            total_ideas_analyzed=len(top_ideas)
        )

    except Exception as e:
        logger.error("Failed to get market insights", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve market insights: {str(e)}")


@router.get("/reports/weekly")
async def get_weekly_reports(
    limit: int = Query(10, ge=1, le=50, description="Number of reports to return"),
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get historical weekly reports."""

    try:
        query = (
            select(WeeklyReportModel)
            .order_by(desc(WeeklyReportModel.week_start))
            .limit(limit)
        )

        result = await db.execute(query)
        reports = result.scalars().all()

        report_responses = []
        for report in reports:
            report_responses.append(WeeklyReportResponse(
                id=str(report.id),
                week_start=report.week_start.isoformat(),
                week_end=report.week_end.isoformat(),
                top_ideas=report.top_ideas,
                market_insights=MarketInsightsResponse(**report.market_insights),
                total_ideas_analyzed=report.total_ideas_analyzed,
                new_ideas_discovered=report.new_ideas_discovered,
                sent_at=report.sent_at.isoformat() if report.sent_at else None,
                delivery_status=report.delivery_status
            ))

        return report_responses

    except Exception as e:
        logger.error("Failed to get weekly reports", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve weekly reports: {str(e)}")


@router.post("/reports/weekly/send")
async def send_weekly_report(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Manually trigger weekly report generation and sending."""

    try:
        def send_report_task():
            import asyncio
            email_service = EmailNotificationService(db)
            asyncio.run(email_service.send_weekly_report())

        background_tasks.add_task(send_report_task)

        return {"message": "Weekly report generation started", "status": "processing"}

    except Exception as e:
        logger.error("Failed to trigger weekly report", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to trigger weekly report: {str(e)}")


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get scheduler status and job information."""

    try:
        from fastapi import Request
        from src.main import app

        # Get scheduler from app state
        scheduler = getattr(app.state, 'scheduler', None)

        if not scheduler:
            # Create a temporary scheduler to get status
            session_factory = get_async_session_factory()
            scheduler = SaaSProjectFinderScheduler(session_factory)

        status = scheduler.get_job_status()
        return SchedulerStatusResponse(**status)

    except Exception as e:
        logger.error("Failed to get scheduler status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")


@router.post("/scheduler/scan")
async def trigger_manual_scan(
    request: ManualTriggerRequest,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant)
):
    """Manually trigger trend scanning."""

    try:
        global scheduler
        if not scheduler:
            session_factory = get_async_session_factory()
            scheduler = SaaSProjectFinderScheduler(session_factory)

        async def scan_task():
            if scheduler is None:
                raise HTTPException(status_code=500, detail="Scheduler not initialized")
            return await scheduler.trigger_manual_scan(request.platform)

        background_tasks.add_task(lambda: asyncio.run(scan_task()))

        return {
            "message": f"Manual scan triggered{' for ' + request.platform if request.platform else ' for all platforms'}",
            "status": "processing"
        }

    except Exception as e:
        logger.error("Failed to trigger manual scan", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to trigger manual scan: {str(e)}")


@router.post("/scheduler/analyze")
async def trigger_manual_analysis(
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant)
):
    """Manually trigger idea analysis."""

    try:
        global scheduler
        if not scheduler:
            session_factory = get_async_session_factory()
            scheduler = SaaSProjectFinderScheduler(session_factory)

        async def analysis_task():
            if scheduler is None:
                raise HTTPException(status_code=500, detail="Scheduler not initialized")
            return await scheduler.trigger_manual_analysis()

        background_tasks.add_task(lambda: asyncio.run(analysis_task()))

        return {"message": "Manual analysis triggered", "status": "processing"}

    except Exception as e:
        logger.error("Failed to trigger manual analysis", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to trigger manual analysis: {str(e)}")


@router.post("/scheduler/ranking")
async def trigger_manual_ranking(
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant)
):
    """Manually trigger ranking update."""

    try:
        global scheduler
        if not scheduler:
            session_factory = get_async_session_factory()
            scheduler = SaaSProjectFinderScheduler(session_factory)

        async def ranking_task():
            if scheduler is None:
                raise HTTPException(status_code=500, detail="Scheduler not initialized")
            return await scheduler.trigger_manual_ranking()

        background_tasks.add_task(lambda: asyncio.run(ranking_task()))

        return {"message": "Manual ranking update triggered", "status": "processing"}

    except Exception as e:
        logger.error("Failed to trigger manual ranking", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to trigger manual ranking: {str(e)}")


@router.get("/platforms")
async def get_supported_platforms(
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get list of supported platforms for SaaS idea discovery."""

    platforms = [
        {
            "id": "producthunt",
            "name": "Product Hunt",
            "description": "Trending product launches and ideas",
            "categories": ["productivity", "developer-tools", "artificial-intelligence", "saas", "no-code"]
        },
        {
            "id": "reddit",
            "name": "Reddit",
            "description": "Startup communities and discussions",
            "categories": ["startups", "entrepreneur", "SaaS", "indiehackers", "microsaas"]
        },
        {
            "id": "indiehackers",
            "name": "Indie Hackers",
            "description": "Bootstrapped project stories and ideas",
            "categories": ["ai", "automation", "saas", "revenue"]
        },
    ]

    return {
        "platforms": platforms,
        "total_platforms": len(platforms)
    }