from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from src.infrastructure.persistence.models import (
    SaaSProjectIdeaModel,
    TrendingMetricsModel,
    SaaSIdeaAnalysisLogModel
)
from src.domain.exceptions import AgentExecutionError

logger = structlog.get_logger()


class SaaSIdeaRankingService:
    """Service for ranking and scoring SaaS project ideas."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

        # Default scoring weights
        self.default_weights = {
            "trend_weight": 0.25,        # 25% - How trending/popular the idea is
            "market_weight": 0.20,       # 20% - Market size and potential
            "ai_suitability_weight": 0.20,  # 20% - How suitable for AI implementation
            "competition_weight": 0.15,   # 15% - Competition level (higher score = less competition)
            "feasibility_weight": 0.10,  # 10% - Implementation difficulty/feasibility
            "monetization_weight": 0.10   # 10% - Revenue/monetization potential
        }

    async def calculate_idea_scores(self, idea_id: str, analysis_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate all scoring metrics for a SaaS idea."""

        try:
            # Extract individual scores from analysis data
            trend_score = self._calculate_trend_score(analysis_data)
            market_score = self._calculate_market_score(analysis_data)
            ai_suitability_score = self._calculate_ai_suitability_score(analysis_data)
            competition_score = self._calculate_competition_score(analysis_data)
            feasibility_score = self._calculate_feasibility_score(analysis_data)
            monetization_score = self._calculate_monetization_score(analysis_data)

            # Calculate composite score using weighted average
            composite_score = self._calculate_composite_score({
                "trend_score": trend_score,
                "market_score": market_score,
                "ai_suitability_score": ai_suitability_score,
                "competition_score": competition_score,
                "feasibility_score": feasibility_score,
                "monetization_score": monetization_score
            })

            scores = {
                "trend_score": trend_score,
                "market_potential_score": market_score,
                "ai_agent_suitability_score": ai_suitability_score,
                "competition_score": competition_score,
                "feasibility_score": feasibility_score,
                "monetization_potential_score": monetization_score,
                "composite_score": composite_score
            }

            logger.info("Calculated scores for SaaS idea",
                       idea_id=idea_id,
                       composite_score=composite_score)

            return scores

        except Exception as e:
            logger.error("Failed to calculate scores for SaaS idea",
                        idea_id=idea_id,
                        error=str(e))
            raise AgentExecutionError(f"Score calculation failed: {str(e)}")

    def _calculate_trend_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate trend momentum score (0-100)."""

        engagement_metrics = analysis_data.get("engagement_metrics", {})
        platform_data = analysis_data.get("platform_data", {})

        # Base score from engagement metrics
        total_engagement = 0
        platform_count = 0

        for platform, metrics in engagement_metrics.items():
            if isinstance(metrics, dict):
                platform_engagement = (
                    metrics.get("likes", 0) +
                    metrics.get("shares", 0) +
                    metrics.get("comments", 0) * 2 +  # Comments weighted higher
                    metrics.get("votes", 0) +
                    metrics.get("upvotes", 0)
                )
                total_engagement += platform_engagement
                platform_count += 1

        if platform_count > 0:
            avg_engagement = total_engagement / platform_count
            base_score = min(100, avg_engagement / 10)  # Normalize to 0-100
        else:
            base_score = 0

        # Apply growth rate multiplier if available
        growth_rate = analysis_data.get("growth_rate", 0)
        growth_multiplier = 1 + (growth_rate / 100)
        trend_score = base_score * growth_multiplier

        # Bonus for multiple platform presence
        if platform_count > 2:
            trend_score *= 1.1

        return max(0, min(100, trend_score))

    def _calculate_market_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate market potential score (0-100)."""

        market_analysis = analysis_data.get("market_analysis", {})

        # Extract market size indicators
        market_size = market_analysis.get("total_addressable_market", "")
        growth_rate = market_analysis.get("growth_rate", "")

        # Base score from market size
        if "B" in market_size:  # Billion dollar market
            size_score = 90
        elif "M" in market_size:  # Million dollar market
            size_score = 70
        else:
            size_score = 40

        # Adjust for growth rate
        if "%" in growth_rate:
            try:
                growth_percent = float(growth_rate.split("%")[0])
                if growth_percent >= 20:
                    growth_bonus = 15
                elif growth_percent >= 10:
                    growth_bonus = 10
                else:
                    growth_bonus = 5
            except:
                growth_bonus = 5
        else:
            growth_bonus = 5

        # Factor in target audience size and accessibility
        target_audience = analysis_data.get("target_audience", "")
        if any(keyword in target_audience.lower() for keyword in ["small business", "smb", "startup"]):
            audience_score = 15  # Good target for micro-SaaS
        elif any(keyword in target_audience.lower() for keyword in ["enterprise", "large"]):
            audience_score = 10  # Harder to reach but high value
        else:
            audience_score = 12

        market_score = size_score + growth_bonus + audience_score
        return max(0, min(100, market_score))

    def _calculate_ai_suitability_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate AI agent suitability score (0-100)."""

        ai_analysis = analysis_data.get("ai_suitability", {})

        # If we have direct AI suitability score, use it
        if "ai_suitability_score" in ai_analysis:
            return min(100, max(0, ai_analysis["ai_suitability_score"]))

        # Otherwise, calculate based on features and complexity
        features = analysis_data.get("extracted_features", [])
        description = analysis_data.get("description", "").lower()

        base_score = 50  # Start with neutral score

        # Boost for AI-friendly features
        ai_indicators = [
            "automation", "ai", "artificial intelligence", "machine learning",
            "nlp", "natural language", "recommendation", "prediction",
            "analysis", "optimization", "classification", "generation"
        ]

        ai_feature_count = sum(1 for indicator in ai_indicators if indicator in description)
        base_score += ai_feature_count * 8

        # Boost for specific automation features
        automation_features = [
            "automation", "workflow", "scheduling", "monitoring",
            "alerts", "notifications", "reporting", "dashboard"
        ]

        automation_count = sum(1 for feature in automation_features if feature in description)
        base_score += automation_count * 5

        # Consider complexity - simpler tasks are better for AI
        complexity = analysis_data.get("estimated_complexity", "medium")
        if complexity == "low":
            base_score += 10
        elif complexity == "high":
            base_score -= 10

        return max(0, min(100, base_score))

    def _calculate_competition_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate competition score (0-100, higher = less competition)."""

        competition_analysis = analysis_data.get("competition_analysis", {})

        # Number of competitors
        competitor_count = competition_analysis.get("competitors_found", 5)

        # Base score inversely related to competitor count
        if competitor_count == 0:
            base_score = 95
        elif competitor_count <= 2:
            base_score = 85
        elif competitor_count <= 5:
            base_score = 70
        elif competitor_count <= 10:
            base_score = 50
        else:
            base_score = 30

        # Adjust for market saturation
        saturation = competition_analysis.get("market_saturation", "medium")
        if saturation == "low":
            saturation_bonus = 15
        elif saturation == "high":
            saturation_bonus = -15
        else:
            saturation_bonus = 0

        # Consider differentiation opportunities
        market_gaps = competition_analysis.get("market_gaps", [])
        differentiation_bonus = min(15, len(market_gaps) * 3)

        competition_score = base_score + saturation_bonus + differentiation_bonus
        return max(0, min(100, competition_score))

    def _calculate_feasibility_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate implementation feasibility score (0-100)."""

        development_estimate = analysis_data.get("development_estimate", {})

        # Base score from development time
        estimated_weeks = development_estimate.get("estimated_development_weeks", 12)

        if estimated_weeks <= 8:
            time_score = 85
        elif estimated_weeks <= 16:
            time_score = 70
        elif estimated_weeks <= 24:
            time_score = 50
        else:
            time_score = 30

        # Adjust for complexity
        complexity = analysis_data.get("estimated_complexity", "medium")
        if complexity == "low":
            complexity_bonus = 10
        elif complexity == "high":
            complexity_bonus = -15
        else:
            complexity_bonus = 0

        # Consider required integrations
        integrations = development_estimate.get("integrations", [])
        integration_penalty = min(20, len(integrations) * 5)

        # Domain availability bonus
        domain_check = analysis_data.get("domain_availability", {})
        if domain_check.get("best_available"):
            domain_bonus = 5
        else:
            domain_bonus = 0

        feasibility_score = time_score + complexity_bonus - integration_penalty + domain_bonus
        return max(0, min(100, feasibility_score))

    def _calculate_monetization_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate monetization potential score (0-100)."""

        # Base score from market and business model indicators
        description = analysis_data.get("description", "").lower()

        base_score = 50

        # Business model indicators
        saas_indicators = [
            "subscription", "monthly", "recurring", "saas", "platform",
            "service", "tool", "dashboard", "api", "integration"
        ]

        model_score = sum(5 for indicator in saas_indicators if indicator in description)
        base_score += min(25, model_score)

        # Value proposition indicators
        value_indicators = [
            "save", "automate", "optimize", "improve", "increase",
            "reduce", "streamline", "efficient", "productivity"
        ]

        value_score = sum(3 for indicator in value_indicators if indicator in description)
        base_score += min(20, value_score)

        # Target market monetization potential
        target_audience = analysis_data.get("target_audience", "").lower()
        if any(keyword in target_audience for keyword in ["business", "company", "enterprise"]):
            base_score += 15  # B2B typically has better monetization
        elif any(keyword in target_audience for keyword in ["developer", "agency", "freelancer"]):
            base_score += 10  # Good willingness to pay for tools

        # Market size influence on monetization
        market_analysis = analysis_data.get("market_analysis", {})
        market_size = market_analysis.get("total_addressable_market", "")
        if "B" in market_size:
            base_score += 10
        elif "M" in market_size:
            base_score += 5

        return max(0, min(100, base_score))

    def _calculate_composite_score(self, scores: Dict[str, float], custom_weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate weighted composite score."""

        weights = custom_weights or self.default_weights

        composite_score = (
            scores["trend_score"] * weights["trend_weight"] +
            scores["market_score"] * weights["market_weight"] +
            scores["ai_suitability_score"] * weights["ai_suitability_weight"] +
            scores["competition_score"] * weights["competition_weight"] +
            scores["feasibility_score"] * weights["feasibility_weight"] +
            scores["monetization_score"] * weights["monetization_weight"]
        )

        return round(composite_score, 2)

    async def update_idea_scores(self, idea_id: str, scores: Dict[str, float]) -> None:
        """Update scores for a SaaS idea in the database."""

        try:
            stmt = (
                update(SaaSProjectIdeaModel)
                .where(SaaSProjectIdeaModel.id == idea_id)
                .values(
                    trend_score=scores.get("trend_score", 0),
                    market_potential_score=scores.get("market_potential_score", 0),
                    ai_agent_suitability_score=scores.get("ai_agent_suitability_score", 0),
                    competition_score=scores.get("competition_score", 0),
                    monetization_potential_score=scores.get("monetization_potential_score", 0),
                    composite_score=scores.get("composite_score", 0),
                    last_analyzed_at=datetime.utcnow()
                )
            )

            await self.db_session.execute(stmt)
            await self.db_session.commit()

            logger.info("Updated scores for SaaS idea",
                       idea_id=idea_id,
                       composite_score=scores.get("composite_score", 0))

        except Exception as e:
            await self.db_session.rollback()
            logger.error("Failed to update scores for SaaS idea",
                        idea_id=idea_id,
                        error=str(e))
            raise

    async def rank_all_ideas(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Rank all active SaaS ideas by composite score."""

        try:
            query = (
                select(SaaSProjectIdeaModel)
                .where(SaaSProjectIdeaModel.is_active == True)
                .order_by(desc(SaaSProjectIdeaModel.composite_score))
            )

            if limit:
                query = query.limit(limit)

            result = await self.db_session.execute(query)
            ideas = result.scalars().all()

            # Update ranking positions
            ranking_updates = []
            for position, idea in enumerate(ideas, 1):
                previous_position = idea.current_ranking_position
                ranking_updates.append({
                    "id": idea.id,
                    "current_position": position,
                    "previous_position": previous_position,
                    "rank_change": (previous_position - position) if previous_position else 0
                })

            # Batch update rankings
            for update_data in ranking_updates:
                stmt = (
                    update(SaaSProjectIdeaModel)
                    .where(SaaSProjectIdeaModel.id == update_data["id"])
                    .values(
                        previous_ranking_position=update_data["previous_position"],
                        current_ranking_position=update_data["current_position"],
                        weekly_rank_change=update_data["rank_change"],
                        last_ranked_at=datetime.utcnow()
                    )
                )
                await self.db_session.execute(stmt)

            await self.db_session.commit()

            # Format results
            ranked_ideas = []
            for idea in ideas:
                ranked_ideas.append({
                    "id": str(idea.id),
                    "title": idea.title,
                    "description": idea.description,
                    "source_platform": idea.source_platform,
                    "composite_score": idea.composite_score,
                    "ranking_position": idea.current_ranking_position,
                    "rank_change": idea.weekly_rank_change,
                    "scores": {
                        "trend": idea.trend_score,
                        "market": idea.market_potential_score,
                        "ai_suitability": idea.ai_agent_suitability_score,
                        "competition": idea.competition_score,
                        "monetization": idea.monetization_potential_score
                    },
                    "discovered_at": idea.discovered_at.isoformat(),
                    "last_analyzed_at": idea.last_analyzed_at.isoformat() if idea.last_analyzed_at else None
                })

            logger.info("Ranked SaaS ideas",
                       total_ideas=len(ranked_ideas),
                       top_score=ranked_ideas[0]["composite_score"] if ranked_ideas else 0)

            return ranked_ideas

        except Exception as e:
            logger.error("Failed to rank SaaS ideas", error=str(e))
            raise AgentExecutionError(f"Ranking failed: {str(e)}")

    async def get_top_ideas(self, limit: int = 10, timeframe_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get top-ranked SaaS ideas, optionally filtered by timeframe."""

        try:
            query = (
                select(SaaSProjectIdeaModel)
                .where(SaaSProjectIdeaModel.is_active == True)
                .order_by(desc(SaaSProjectIdeaModel.composite_score))
                .limit(limit)
            )

            if timeframe_days:
                cutoff_date = datetime.utcnow() - timedelta(days=timeframe_days)
                query = query.where(SaaSProjectIdeaModel.discovered_at >= cutoff_date)

            result = await self.db_session.execute(query)
            ideas = result.scalars().all()

            top_ideas = []
            for idea in ideas:
                top_ideas.append({
                    "id": str(idea.id),
                    "title": idea.title,
                    "description": idea.description,
                    "source_url": idea.source_url,
                    "source_platform": idea.source_platform,
                    "composite_score": idea.composite_score,
                    "ranking_position": idea.current_ranking_position,
                    "scores": {
                        "trend": idea.trend_score,
                        "market": idea.market_potential_score,
                        "ai_suitability": idea.ai_agent_suitability_score,
                        "competition": idea.competition_score,
                        "monetization": idea.monetization_potential_score
                    },
                    "tags": idea.tags,
                    "estimated_market_size": idea.estimated_market_size,
                    "implementation_difficulty": idea.implementation_difficulty,
                    "discovered_at": idea.discovered_at.isoformat(),
                    "analysis_data": idea.analysis_data
                })

            return top_ideas

        except Exception as e:
            logger.error("Failed to get top SaaS ideas", error=str(e))
            raise AgentExecutionError(f"Failed to get top ideas: {str(e)}")

    async def get_trending_ideas(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get ideas with highest trend momentum."""

        try:
            query = (
                select(SaaSProjectIdeaModel)
                .where(SaaSProjectIdeaModel.is_active == True)
                .order_by(desc(SaaSProjectIdeaModel.trend_score))
                .limit(limit)
            )

            result = await self.db_session.execute(query)
            ideas = result.scalars().all()

            trending_ideas = []
            for idea in ideas:
                trending_ideas.append({
                    "id": str(idea.id),
                    "title": idea.title,
                    "description": idea.description,
                    "trend_score": idea.trend_score,
                    "composite_score": idea.composite_score,
                    "source_platform": idea.source_platform,
                    "engagement_metrics": idea.engagement_metrics,
                    "discovered_at": idea.discovered_at.isoformat()
                })

            return trending_ideas

        except Exception as e:
            logger.error("Failed to get trending SaaS ideas", error=str(e))
            raise AgentExecutionError(f"Failed to get trending ideas: {str(e)}")