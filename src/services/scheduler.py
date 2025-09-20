from typing import Dict, Any, Optional, List
from datetime import datetime, time
import asyncio
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.ai.agent_executor import AgentExecutor
from src.infrastructure.ai.openai_client import OpenAIClientWrapper
from src.infrastructure.ai.tool_executor import ToolExecutor
from src.infrastructure.persistence.database import get_db_session
from src.services.ranking_service import SaaSIdeaRankingService
from src.services.email_service import EmailNotificationService
from src.infrastructure.persistence.models import SaaSProjectIdeaModel, SaaSIdeaAnalysisLogModel
from sqlalchemy import select, insert
from uuid import uuid4

logger = structlog.get_logger()


class SaaSProjectFinderScheduler:
    """Scheduler for automated SaaS project discovery and analysis tasks."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.scheduler = AsyncIOScheduler()
        self.agent_executor = None  # Will be initialized when needed

    async def start(self):
        """Start the scheduler with all tasks."""

        try:
            # Schedule daily scanning tasks
            self._schedule_daily_tasks()

            # Schedule weekly tasks
            self._schedule_weekly_tasks()

            # Schedule ranking updates
            self._schedule_ranking_tasks()

            # Start the scheduler
            self.scheduler.start()

            logger.info("SaaS Project Finder scheduler started successfully")

        except Exception as e:
            logger.error("Failed to start scheduler", error=str(e))
            raise

    def _schedule_daily_tasks(self):
        """Schedule daily scanning and analysis tasks."""

        # Morning scan (9 AM UTC) - Discover new ideas
        self.scheduler.add_job(
            func=self.daily_trend_scanning,
            trigger=CronTrigger(hour=9, minute=0),
            id="daily_trend_scanning",
            name="Daily Trend Scanning",
            max_instances=1,
            coalesce=True
        )

        # Afternoon analysis (2 PM UTC) - Analyze discovered ideas
        self.scheduler.add_job(
            func=self.daily_idea_analysis,
            trigger=CronTrigger(hour=14, minute=0),
            id="daily_idea_analysis",
            name="Daily Idea Analysis",
            max_instances=1,
            coalesce=True
        )

        # Evening ranking (6 PM UTC) - Update rankings
        self.scheduler.add_job(
            func=self.daily_ranking_update,
            trigger=CronTrigger(hour=18, minute=0),
            id="daily_ranking_update",
            name="Daily Ranking Update",
            max_instances=1,
            coalesce=True
        )

        logger.info("Scheduled daily tasks")

    def _schedule_weekly_tasks(self):
        """Schedule weekly report generation and email tasks."""

        # Weekly report (Sunday 10 AM UTC)
        self.scheduler.add_job(
            func=self.weekly_report_generation,
            trigger=CronTrigger(day_of_week='sun', hour=10, minute=0),
            id="weekly_report_generation",
            name="Weekly Report Generation",
            max_instances=1,
            coalesce=True
        )

        logger.info("Scheduled weekly tasks")

    def _schedule_ranking_tasks(self):
        """Schedule ranking and scoring update tasks."""

        # Continuous ranking updates every 4 hours
        self.scheduler.add_job(
            func=self.update_all_rankings,
            trigger=IntervalTrigger(hours=4),
            id="update_all_rankings",
            name="Update All Rankings",
            max_instances=1,
            coalesce=True
        )

        logger.info("Scheduled ranking tasks")

    async def daily_trend_scanning(self):
        """Execute daily trend scanning across all platforms."""

        logger.info("Starting daily trend scanning")

        try:
            async with self.session_factory() as session:
                # Execute trend scanner agent for each platform
                platforms = ["producthunt", "reddit", "indiehackers"]

                for platform in platforms:
                    await self._execute_trend_scanning(session, platform)

                logger.info("Daily trend scanning completed successfully")

        except Exception as e:
            logger.error("Daily trend scanning failed", error=str(e))

    async def _execute_trend_scanning(self, session: AsyncSession, platform: str):
        """Execute trend scanning for a specific platform."""

        try:
            if not self.agent_executor:
                openai_client = OpenAIClientWrapper()
                tool_executor = ToolExecutor()
                self.agent_executor = AgentExecutor(openai_client, tool_executor)

            # Configure parameters based on platform
            platform_configs = {
                "producthunt": {
                    "scan_platforms": ["producthunt"],
                    "focus_categories": ["productivity", "ai", "automation", "developer-tools"],
                    "timeframe": "day",
                    "min_engagement": 20
                },
                "reddit": {
                    "scan_platforms": ["reddit"],
                    "focus_categories": ["saas", "micro-saas", "startup", "ai"],
                    "timeframe": "day",
                    "min_engagement": 15
                },
                "indiehackers": {
                    "scan_platforms": ["indiehackers"],
                    "focus_categories": ["ai", "automation", "saas", "revenue"],
                    "timeframe": "day",
                    "min_engagement": 10
                }
            }

            # TODO: Properly implement agent execution with correct Agent and Tenant objects
            # Execute the trend scanner agent
            # result = await self.agent_executor.execute_sync(
            #     agent=agent_obj,  # Need to create Agent object from config
            #     parameters=platform_configs.get(platform, platform_configs["producthunt"]),
            #     tenant=system_tenant  # Need to create system tenant
            # )
            result = None  # Temporary placeholder

            # Process and store discovered ideas
            if result and result.get("status") == "completed":
                await self._process_discovered_ideas(session, result.get("result", {}), platform)

            logger.info("Platform trend scanning completed",
                       platform=platform,
                       ideas_found=len(result.get("result", {}).get("discovered_ideas", [])) if result else 0)

        except Exception as e:
            logger.error("Platform trend scanning failed",
                        platform=platform,
                        error=str(e))

    async def _process_discovered_ideas(self, session: AsyncSession, scanner_result: Dict[str, Any], platform: str):
        """Process and store newly discovered ideas."""

        discovered_ideas: List[Dict[str, Any]] = scanner_result.get("discovered_ideas", [])

        for idea_data in discovered_ideas:
            try:
                # Check if idea already exists
                existing_query = select(SaaSProjectIdeaModel).where(
                    SaaSProjectIdeaModel.source_url == idea_data.get("source_url", "")
                )
                result = await session.execute(existing_query)
                existing_idea = result.scalar_one_or_none()

                if existing_idea:
                    # Update engagement metrics for existing idea
                    existing_idea.engagement_metrics = idea_data.get("engagement_metrics", {})
                    continue

                # Create new idea record
                new_idea = SaaSProjectIdeaModel(
                    id=uuid4(),
                    title=idea_data.get("title", ""),
                    description=idea_data.get("description", ""),
                    source_url=idea_data.get("source_url", ""),
                    source_platform=platform,
                    tags=idea_data.get("tags", []),
                    engagement_metrics=idea_data.get("engagement_metrics", {}),
                    analysis_data=idea_data,
                    discovered_at=datetime.utcnow()
                )

                session.add(new_idea)

                logger.info("Stored new SaaS idea",
                           title=new_idea.title,
                           platform=platform)

            except Exception as e:
                logger.error("Failed to process discovered idea",
                            idea_title=idea_data.get("title", "Unknown"),
                            error=str(e))

        await session.commit()

    async def daily_idea_analysis(self):
        """Execute daily analysis of discovered ideas."""

        logger.info("Starting daily idea analysis")

        try:
            async with self.session_factory() as session:
                # Get ideas that need analysis (discovered in last 48 hours, not analyzed)
                cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                cutoff_date = cutoff_date.replace(day=cutoff_date.day - 2)  # Last 2 days

                query = select(SaaSProjectIdeaModel).where(
                    SaaSProjectIdeaModel.discovered_at >= cutoff_date,
                    SaaSProjectIdeaModel.last_analyzed_at.is_(None),
                    SaaSProjectIdeaModel.is_active == True
                )

                result = await session.execute(query)
                ideas_to_analyze = result.scalars().all()

                logger.info("Found ideas to analyze", count=len(ideas_to_analyze))

                # Analyze each idea
                for idea in ideas_to_analyze:
                    await self._analyze_single_idea(session, idea)

                logger.info("Daily idea analysis completed successfully",
                           analyzed_count=len(ideas_to_analyze))

        except Exception as e:
            logger.error("Daily idea analysis failed", error=str(e))

    async def _analyze_single_idea(self, session: AsyncSession, idea: SaaSProjectIdeaModel):
        """Analyze a single SaaS idea."""

        try:
            if not self.agent_executor:
                openai_client = OpenAIClientWrapper()
                tool_executor = ToolExecutor()
                self.agent_executor = AgentExecutor(openai_client, tool_executor)

            # TODO: Properly implement agent execution with correct Agent and Tenant objects
            # Execute idea analyzer agent
            # analysis_result = await self.agent_executor.execute_sync(
            #     agent=agent_obj,  # Need to create Agent object from config
            #     parameters={
            #         "idea_id": str(idea.id),
            #         "idea_title": idea.title,
            #         "idea_description": idea.description,
            #         "analysis_depth": "standard",
            #         "focus_areas": ["market", "competition", "ai-suitability", "monetization"]
            #     },
            #     tenant=system_tenant  # Need to create system tenant
            # )
            analysis_result = None  # Temporary placeholder

            if analysis_result and analysis_result.get("status") == "completed":
                # Update idea with analysis data
                analysis_data = analysis_result.get("result", {})
                idea.analysis_data.update(analysis_data)
                idea.last_analyzed_at = datetime.utcnow()

                # Calculate and update scores
                ranking_service = SaaSIdeaRankingService(session)
                scores = await ranking_service.calculate_idea_scores(str(idea.id), idea.analysis_data)
                await ranking_service.update_idea_scores(str(idea.id), scores)

                # Log analysis
                analysis_log = SaaSIdeaAnalysisLogModel(
                    id=uuid4(),
                    project_idea_id=idea.id,
                    agent_id="saas-idea-analyzer",
                    analysis_type="analysis",
                    input_parameters={"idea_title": idea.title, "idea_description": idea.description},
                    analysis_results=analysis_data,
                    scores_generated=scores,
                    execution_time_ms=analysis_result.get("execution_time_ms", 0),
                    tokens_used=analysis_result.get("token_usage", 0),
                    success=True,
                    created_at=datetime.utcnow()
                )
                session.add(analysis_log)

                # Check for immediate alerts (exceptional ideas)
                if scores.get("composite_score", 0) >= 85:
                    email_service = EmailNotificationService(session)
                    await email_service.send_immediate_alert({
                        "title": idea.title,
                        "description": idea.description,
                        "source_platform": idea.source_platform,
                        "source_url": idea.source_url,
                        "composite_score": scores.get("composite_score", 0),
                        "scores": {
                            "ai_suitability": scores.get("ai_agent_suitability_score", 0),
                            "market": scores.get("market_potential_score", 0),
                            "competition": scores.get("competition_score", 0)
                        }
                    }, "high_potential")

                logger.info("Analyzed SaaS idea",
                           idea_title=idea.title,
                           composite_score=scores.get("composite_score", 0))

        except Exception as e:
            logger.error("Failed to analyze SaaS idea",
                        idea_title=idea.title,
                        error=str(e))

            # Log failed analysis
            analysis_log = SaaSIdeaAnalysisLogModel(
                id=uuid4(),
                project_idea_id=idea.id,
                agent_id="saas-idea-analyzer",
                analysis_type="analysis",
                input_parameters={"idea_title": idea.title},
                analysis_results={},
                scores_generated={},
                execution_time_ms=0,
                tokens_used=0,
                success=False,
                error_message=str(e),
                created_at=datetime.utcnow()
            )
            session.add(analysis_log)

        await session.commit()

    async def daily_ranking_update(self):
        """Execute daily ranking updates."""

        logger.info("Starting daily ranking update")

        try:
            async with self.session_factory() as session:
                ranking_service = SaaSIdeaRankingService(session)

                # Rank all ideas
                ranked_ideas = await ranking_service.rank_all_ideas()

                logger.info("Daily ranking update completed successfully",
                           total_ranked=len(ranked_ideas),
                           top_score=ranked_ideas[0]["composite_score"] if ranked_ideas else 0)

        except Exception as e:
            logger.error("Daily ranking update failed", error=str(e))

    async def update_all_rankings(self):
        """Update rankings for all ideas (scheduled every 4 hours)."""

        logger.info("Starting periodic ranking update")

        try:
            async with self.session_factory() as session:
                ranking_service = SaaSIdeaRankingService(session)
                await ranking_service.rank_all_ideas()

                logger.info("Periodic ranking update completed")

        except Exception as e:
            logger.error("Periodic ranking update failed", error=str(e))

    async def weekly_report_generation(self):
        """Generate and send weekly report."""

        logger.info("Starting weekly report generation")

        try:
            async with self.session_factory() as session:
                email_service = EmailNotificationService(session)

                # Send weekly report
                success = await email_service.send_weekly_report()

                if success:
                    logger.info("Weekly report sent successfully")
                else:
                    logger.error("Failed to send weekly report")

        except Exception as e:
            logger.error("Weekly report generation failed", error=str(e))

    async def stop(self):
        """Stop the scheduler."""

        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("SaaS Project Finder scheduler stopped")

        except Exception as e:
            logger.error("Failed to stop scheduler", error=str(e))

    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs."""

        jobs_status: Dict[str, Any] = {}

        for job in self.scheduler.get_jobs():
            jobs_status[job.id] = {
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "active": True
            }

        return {
            "scheduler_running": self.scheduler.running,
            "jobs": jobs_status,
            "total_jobs": len(jobs_status)
        }

    async def trigger_manual_scan(self, platform: Optional[str] = None) -> Dict[str, Any]:
        """Manually trigger a scan for testing purposes."""

        try:
            async with self.session_factory() as session:
                if platform:
                    await self._execute_trend_scanning(session, platform)
                    return {"status": "success", "message": f"Manual scan triggered for {platform}"}
                else:
                    await self.daily_trend_scanning()
                    return {"status": "success", "message": "Manual scan triggered for all platforms"}

        except Exception as e:
            logger.error("Manual scan failed", platform=platform, error=str(e))
            return {"status": "error", "message": str(e)}

    async def trigger_manual_analysis(self) -> Dict[str, Any]:
        """Manually trigger idea analysis for testing purposes."""

        try:
            await self.daily_idea_analysis()
            return {"status": "success", "message": "Manual analysis triggered"}

        except Exception as e:
            logger.error("Manual analysis failed", error=str(e))
            return {"status": "error", "message": str(e)}

    async def trigger_manual_ranking(self) -> Dict[str, Any]:
        """Manually trigger ranking update for testing purposes."""

        try:
            await self.daily_ranking_update()
            return {"status": "success", "message": "Manual ranking update triggered"}

        except Exception as e:
            logger.error("Manual ranking failed", error=str(e))
            return {"status": "error", "message": str(e)}