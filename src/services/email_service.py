from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json

from src.infrastructure.persistence.models import WeeklyReportModel, SaaSProjectIdeaModel
from src.services.ranking_service import SaaSIdeaRankingService
from src.domain.exceptions import AgentExecutionError

logger = structlog.get_logger()


class EmailNotificationService:
    """Service for sending email notifications about SaaS ideas."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.ranking_service = SaaSIdeaRankingService(db_session)

        # Email configuration
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_username = os.getenv("EMAIL_USERNAME", "")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")
        self.from_address = os.getenv("EMAIL_FROM_ADDRESS", "saas-finder@example.com")

        # Default recipients
        self.default_recipients = self._parse_recipients(
            os.getenv("EMAIL_REPORT_RECIPIENTS", "admin@example.com")
        )

    def _parse_recipients(self, recipients_str: str) -> List[str]:
        """Parse comma-separated email recipients."""
        return [email.strip() for email in recipients_str.split(",") if email.strip()]

    async def generate_weekly_report(self, week_start: date, week_end: date) -> Dict[str, Any]:
        """Generate weekly report data for SaaS ideas."""

        try:
            # Get top ideas for the week
            top_ideas = await self.ranking_service.get_top_ideas(limit=10)

            # Get trending ideas
            trending_ideas = await self.ranking_service.get_trending_ideas(limit=5)

            # Get ideas discovered this week
            new_ideas_query = (
                select(SaaSProjectIdeaModel)
                .where(
                    SaaSProjectIdeaModel.discovered_at >= datetime.combine(week_start, datetime.min.time()),
                    SaaSProjectIdeaModel.discovered_at <= datetime.combine(week_end, datetime.max.time()),
                    SaaSProjectIdeaModel.is_active == True
                )
            )
            result = await self.db_session.execute(new_ideas_query)
            new_ideas = result.scalars().all()

            # Analyze trending categories
            category_counts = {}
            for idea in top_ideas:
                for tag in idea.get("tags", []):
                    category_counts[tag] = category_counts.get(tag, 0) + 1

            trending_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]

            # Generate market insights
            market_insights = self._generate_market_insights(top_ideas, trending_ideas)

            # Format top ideas for report
            formatted_top_ideas = []
            for i, idea in enumerate(top_ideas, 1):
                formatted_top_ideas.append({
                    "rank": i,
                    "title": idea["title"],
                    "description": idea["description"][:200] + "..." if len(idea["description"]) > 200 else idea["description"],
                    "composite_score": idea["composite_score"],
                    "source_platform": idea["source_platform"],
                    "ai_suitability": idea["scores"]["ai_suitability"],
                    "market_score": idea["scores"]["market"],
                    "trend_score": idea["scores"]["trend"],
                    "why_trending": self._explain_trending_reason(idea),
                    "implementation_notes": self._generate_implementation_notes(idea),
                    "estimated_market_size": idea.get("estimated_market_size", "Unknown")
                })

            report_data = {
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "top_ideas": formatted_top_ideas,
                "trending_ideas": trending_ideas,
                "market_insights": market_insights,
                "trending_categories": [cat[0] for cat in trending_categories],
                "total_ideas_analyzed": len(top_ideas),
                "new_ideas_discovered": len(new_ideas),
                "generated_at": datetime.utcnow().isoformat()
            }

            logger.info("Generated weekly report",
                       week_start=week_start,
                       week_end=week_end,
                       top_ideas_count=len(formatted_top_ideas),
                       new_ideas_count=len(new_ideas))

            return report_data

        except Exception as e:
            logger.error("Failed to generate weekly report",
                        week_start=week_start,
                        week_end=week_end,
                        error=str(e))
            raise AgentExecutionError(f"Weekly report generation failed: {str(e)}")

    def _generate_market_insights(self, top_ideas: List[Dict], trending_ideas: List[Dict]) -> Dict[str, Any]:
        """Generate market insights from top and trending ideas."""

        insights = {
            "dominant_trends": [],
            "emerging_opportunities": [],
            "ai_adoption_patterns": [],
            "market_gaps": []
        }

        # Analyze dominant trends
        ai_count = sum(1 for idea in top_ideas if idea["scores"]["ai_suitability"] > 70)
        automation_count = sum(1 for idea in top_ideas if "automation" in str(idea.get("tags", [])).lower())

        if ai_count > 5:
            insights["dominant_trends"].append("Strong focus on AI-powered solutions")
        if automation_count > 3:
            insights["dominant_trends"].append("Automation tools gaining significant traction")

        # Identify emerging opportunities
        high_market_low_competition = [
            idea for idea in top_ideas
            if idea["scores"]["market"] > 70 and idea["scores"]["competition"] > 60
        ]

        if high_market_low_competition:
            insights["emerging_opportunities"].append({
                "opportunity": "High market potential with low competition",
                "count": len(high_market_low_competition),
                "examples": [idea["title"] for idea in high_market_low_competition[:2]]
            })

        # AI adoption patterns
        avg_ai_score = sum(idea["scores"]["ai_suitability"] for idea in top_ideas) / len(top_ideas)
        insights["ai_adoption_patterns"].append(f"Average AI suitability score: {avg_ai_score:.1f}/100")

        # Market gaps analysis
        low_competition_areas = [
            idea for idea in top_ideas
            if idea["scores"]["competition"] > 80
        ]

        if low_competition_areas:
            insights["market_gaps"] = [idea["title"] for idea in low_competition_areas[:3]]

        return insights

    def _explain_trending_reason(self, idea: Dict[str, Any]) -> str:
        """Generate explanation for why an idea is trending."""

        scores = idea["scores"]
        reasons = []

        if scores["trend"] > 80:
            reasons.append("High social media engagement")
        if scores["ai_suitability"] > 75:
            reasons.append("Perfect fit for AI implementation")
        if scores["market"] > 70:
            reasons.append("Large addressable market")
        if scores["competition"] > 70:
            reasons.append("Limited existing competition")

        if not reasons:
            reasons.append("Solid overall potential")

        return ", ".join(reasons)

    def _generate_implementation_notes(self, idea: Dict[str, Any]) -> str:
        """Generate implementation notes for an idea."""

        scores = idea["scores"]
        difficulty = idea.get("implementation_difficulty", "medium")

        notes = []

        if difficulty == "easy":
            notes.append("Quick to prototype")
        elif difficulty == "hard":
            notes.append("Complex implementation required")

        if scores["ai_suitability"] > 80:
            notes.append("AI agents can handle most functionality")
        elif scores["ai_suitability"] > 60:
            notes.append("Good candidate for AI enhancement")

        if scores["market"] > 80:
            notes.append("High revenue potential")

        return "; ".join(notes) if notes else "Standard implementation approach"

    def _create_html_email(self, report_data: Dict[str, Any]) -> str:
        """Create HTML email content from report data."""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .idea-card {{ border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 8px; }}
                .score-badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }}
                .score-excellent {{ background-color: #28a745; }}
                .score-good {{ background-color: #17a2b8; }}
                .score-average {{ background-color: #ffc107; color: #333; }}
                .score-poor {{ background-color: #dc3545; }}
                .metrics {{ display: flex; gap: 10px; margin: 10px 0; }}
                .metric {{ background: #f8f9fa; padding: 5px 10px; border-radius: 4px; font-size: 0.9em; }}
                .insights {{ background: #e9ecef; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Weekly SaaS Project Ideas Report</h1>
                <p>Week of {report_data['week_start']} to {report_data['week_end']}</p>
            </div>

            <div class="content">
                <h2>📊 Weekly Summary</h2>
                <ul>
                    <li><strong>{report_data['total_ideas_analyzed']}</strong> ideas analyzed</li>
                    <li><strong>{report_data['new_ideas_discovered']}</strong> new ideas discovered this week</li>
                    <li><strong>Top trending categories:</strong> {', '.join(report_data['trending_categories'][:3])}</li>
                </ul>

                <h2>🏆 Top 10 SaaS Ideas This Week</h2>
        """

        # Add top ideas
        for idea in report_data['top_ideas']:
            score_class = (
                "score-excellent" if idea['composite_score'] >= 80 else
                "score-good" if idea['composite_score'] >= 65 else
                "score-average" if idea['composite_score'] >= 50 else
                "score-poor"
            )

            html += f"""
                <div class="idea-card">
                    <h3>#{idea['rank']} {idea['title']}
                        <span class="score-badge {score_class}">{idea['composite_score']:.1f}/100</span>
                    </h3>
                    <p>{idea['description']}</p>

                    <div class="metrics">
                        <span class="metric">🔥 Trend: {idea['trend_score']:.0f}</span>
                        <span class="metric">🎯 Market: {idea['market_score']:.0f}</span>
                        <span class="metric">🤖 AI Fit: {idea['ai_suitability']:.0f}</span>
                        <span class="metric">📈 Market Size: {idea['estimated_market_size']}</span>
                    </div>

                    <p><strong>Why it's trending:</strong> {idea['why_trending']}</p>
                    <p><strong>Implementation notes:</strong> {idea['implementation_notes']}</p>
                    <p><small>Source: {idea['source_platform'].title()}</small></p>
                </div>
            """

        # Add market insights
        html += f"""
                <div class="insights">
                    <h2>💡 Market Insights</h2>
                    <h4>Dominant Trends:</h4>
                    <ul>
        """

        for trend in report_data['market_insights']['dominant_trends']:
            html += f"<li>{trend}</li>"

        html += "</ul><h4>Emerging Opportunities:</h4><ul>"

        for opportunity in report_data['market_insights']['emerging_opportunities']:
            html += f"<li>{opportunity['opportunity']} ({opportunity['count']} ideas)</li>"

        html += f"""
                    </ul>
                    <h4>AI Adoption Patterns:</h4>
                    <ul>
        """

        for pattern in report_data['market_insights']['ai_adoption_patterns']:
            html += f"<li>{pattern}</li>"

        html += """
                    </ul>
                </div>

                <div class="footer">
                    <p>Generated by SaaS Project Finder AI Backend</p>
                    <p>This report is automatically generated weekly based on trending discussions across multiple platforms.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _create_text_email(self, report_data: Dict[str, Any]) -> str:
        """Create plain text email content from report data."""

        text = f"""
WEEKLY SAAS PROJECT IDEAS REPORT
Week of {report_data['week_start']} to {report_data['week_end']}

WEEKLY SUMMARY
==============
- {report_data['total_ideas_analyzed']} ideas analyzed
- {report_data['new_ideas_discovered']} new ideas discovered this week
- Top trending categories: {', '.join(report_data['trending_categories'][:3])}

TOP 10 SAAS IDEAS THIS WEEK
============================
"""

        for idea in report_data['top_ideas']:
            text += f"""
#{idea['rank']} {idea['title']} (Score: {idea['composite_score']:.1f}/100)
{'-' * 50}
{idea['description']}

Metrics: Trend {idea['trend_score']:.0f} | Market {idea['market_score']:.0f} | AI Fit {idea['ai_suitability']:.0f}
Market Size: {idea['estimated_market_size']}
Why trending: {idea['why_trending']}
Implementation: {idea['implementation_notes']}
Source: {idea['source_platform'].title()}

"""

        text += f"""
MARKET INSIGHTS
===============
Dominant Trends:
{chr(10).join('- ' + trend for trend in report_data['market_insights']['dominant_trends'])}

Emerging Opportunities:
{chr(10).join('- ' + opp['opportunity'] + f" ({opp['count']} ideas)" for opp in report_data['market_insights']['emerging_opportunities'])}

AI Adoption Patterns:
{chr(10).join('- ' + pattern for pattern in report_data['market_insights']['ai_adoption_patterns'])}

---
Generated by SaaS Project Finder AI Backend
This report is automatically generated weekly based on trending discussions across multiple platforms.
"""

        return text

    async def send_weekly_report(self, recipients: Optional[List[str]] = None) -> bool:
        """Send weekly report via email."""

        try:
            # Calculate week dates (previous Sunday to Saturday)
            today = date.today()
            week_start = today - timedelta(days=today.weekday() + 1)  # Last Sunday
            week_end = week_start + timedelta(days=6)  # Last Saturday

            # Generate report data
            report_data = await self.generate_weekly_report(week_start, week_end)

            # Create email content
            html_content = self._create_html_email(report_data)
            text_content = self._create_text_email(report_data)

            # Send email
            recipients = recipients or self.default_recipients
            success = await self._send_email(
                recipients=recipients,
                subject=f"Weekly SaaS Ideas Report - {week_start} to {week_end}",
                html_content=html_content,
                text_content=text_content
            )

            # Save report to database
            if success:
                await self._save_weekly_report(week_start, week_end, report_data, recipients)

            return success

        except Exception as e:
            logger.error("Failed to send weekly report", error=str(e))
            return False

    async def _send_email(self, recipients: List[str], subject: str, html_content: str, text_content: str) -> bool:
        """Send email using SMTP."""

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_address
            msg['To'] = ', '.join(recipients)

            # Add text and HTML parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')

            msg.attach(part1)
            msg.attach(part2)

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            server.send_message(msg)
            server.quit()

            logger.info("Weekly report email sent successfully",
                       recipients=recipients,
                       subject=subject)

            return True

        except Exception as e:
            logger.error("Failed to send email",
                        recipients=recipients,
                        subject=subject,
                        error=str(e))
            return False

    async def _save_weekly_report(self, week_start: date, week_end: date, report_data: Dict[str, Any], recipients: List[str]) -> None:
        """Save weekly report to database."""

        try:
            stmt = insert(WeeklyReportModel).values(
                week_start=week_start,
                week_end=week_end,
                top_ideas=report_data['top_ideas'],
                market_insights=report_data['market_insights'],
                trending_categories=report_data['trending_categories'],
                total_ideas_analyzed=report_data['total_ideas_analyzed'],
                new_ideas_discovered=report_data['new_ideas_discovered'],
                recipient_emails=recipients,
                sent_at=datetime.utcnow(),
                delivery_status="sent",
                generated_at=datetime.utcnow()
            )

            await self.db_session.execute(stmt)
            await self.db_session.commit()

            logger.info("Saved weekly report to database",
                       week_start=week_start,
                       week_end=week_end)

        except Exception as e:
            logger.error("Failed to save weekly report to database",
                        week_start=week_start,
                        week_end=week_end,
                        error=str(e))
            # Don't raise - email was sent successfully

    async def send_daily_report(self, recipients: Optional[List[str]] = None) -> bool:
        """Send daily report email with new ideas from today."""

        try:
            # Get today's date
            today = date.today()

            # Get ideas discovered today
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())

            new_ideas_query = (
                select(SaaSProjectIdeaModel)
                .where(
                    SaaSProjectIdeaModel.discovered_at >= today_start,
                    SaaSProjectIdeaModel.discovered_at <= today_end,
                    SaaSProjectIdeaModel.is_active == True
                )
            )
            result = await self.db_session.execute(new_ideas_query)
            new_ideas = result.scalars().all()

            if not new_ideas:
                logger.info("No new ideas discovered today, skipping daily report")
                return True

            # Get ranked analysis for today's ideas
            ranked_ideas = []
            for idea in new_ideas:
                if idea.analysis_data and isinstance(idea.analysis_data, dict):
                    ai_score = idea.analysis_data.get('ai_suitability_score', 0)
                    ranked_ideas.append({
                        'title': idea.title,
                        'description': idea.description,
                        'source_platform': idea.source_platform,
                        'source_url': idea.source_url,
                        'ai_score': ai_score,
                        'discovered_at': idea.discovered_at,
                        'analysis': idea.analysis_data
                    })

            # Sort by AI suitability score
            ranked_ideas.sort(key=lambda x: x['ai_score'], reverse=True)

            # Create email content
            html_content = self._create_daily_html_email(today, ranked_ideas)
            text_content = self._create_daily_text_email(today, ranked_ideas)

            # Send email
            recipients = recipients or self.default_recipients
            success = await self._send_email(
                recipients=recipients,
                subject=f"Daily SaaS Ideas Report - {today.strftime('%B %d, %Y')} ({len(ranked_ideas)} new ideas)",
                html_content=html_content,
                text_content=text_content
            )

            logger.info("Daily report email sent",
                       date=today,
                       ideas_count=len(ranked_ideas),
                       success=success)

            return success

        except Exception as e:
            logger.error("Failed to send daily report", error=str(e))
            return False

    def _create_daily_html_email(self, report_date: date, ranked_ideas: List[Dict[str, Any]]) -> str:
        """Create HTML email content for daily report."""

        high_priority = [idea for idea in ranked_ideas if idea['ai_score'] >= 75]
        medium_priority = [idea for idea in ranked_ideas if 60 <= idea['ai_score'] < 75]
        low_priority = [idea for idea in ranked_ideas if idea['ai_score'] < 60]

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .idea-card {{ border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 8px; }}
                .priority-high {{ border-left: 4px solid #28a745; }}
                .priority-medium {{ border-left: 4px solid #ffc107; }}
                .priority-low {{ border-left: 4px solid #6c757d; }}
                .score-badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }}
                .score-high {{ background-color: #28a745; }}
                .score-medium {{ background-color: #ffc107; color: #333; }}
                .score-low {{ background-color: #6c757d; }}
                .summary {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Daily SaaS Ideas Report</h1>
                <p>{report_date.strftime('%A, %B %d, %Y')}</p>
            </div>

            <div class="content">
                <div class="summary">
                    <h2>Daily Summary</h2>
                    <ul>
                        <li><strong>{len(ranked_ideas)}</strong> new ideas discovered today</li>
                        <li><strong>{len(high_priority)}</strong> high-priority ideas (AI score ≥75)</li>
                        <li><strong>{len(medium_priority)}</strong> medium-priority ideas (AI score 60-74)</li>
                        <li><strong>{len(low_priority)}</strong> lower-priority ideas (AI score <60)</li>
                    </ul>
                </div>
        """

        if high_priority:
            html += "<h2>🔥 High Priority Ideas (AI Score ≥75)</h2>"
            for idea in high_priority:
                html += self._format_daily_idea_html(idea, "high", "priority-high")

        if medium_priority:
            html += "<h2>⭐ Medium Priority Ideas (AI Score 60-74)</h2>"
            for idea in medium_priority:
                html += self._format_daily_idea_html(idea, "medium", "priority-medium")

        if low_priority:
            html += "<h2>📝 Other Ideas (AI Score <60)</h2>"
            for idea in low_priority:
                html += self._format_daily_idea_html(idea, "low", "priority-low")

        html += """
                <div class="footer">
                    <p>Generated by SaaS Project Finder AI Backend</p>
                    <p>This daily report includes all new ideas discovered in the last 24 hours with AI analysis and ranking.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _format_daily_idea_html(self, idea: Dict[str, Any], priority: str, css_class: str) -> str:
        """Format a single idea for daily HTML email."""

        score_class = f"score-{priority}"
        analysis = idea.get('analysis', {})

        return f"""
            <div class="idea-card {css_class}">
                <h3>{idea['title']}
                    <span class="score-badge {score_class}">AI Score: {idea['ai_score']:.0f}/100</span>
                </h3>
                <p>{idea['description']}</p>

                <p><strong>Analysis Summary:</strong></p>
                <ul>
                    <li><strong>Market Potential:</strong> {analysis.get('market_potential', 'Not analyzed')}</li>
                    <li><strong>AI Implementation:</strong> {analysis.get('ai_implementation_notes', 'Not analyzed')}</li>
                    <li><strong>Competition Level:</strong> {analysis.get('competition_analysis', 'Not analyzed')}</li>
                    <li><strong>Revenue Potential:</strong> {analysis.get('monetization_potential', 'Not analyzed')}</li>
                </ul>

                <p><strong>Source:</strong> {idea['source_platform'].title()} -
                   <a href="{idea.get('source_url', '#')}">View Original</a></p>
                <p><small>Discovered: {idea['discovered_at'].strftime('%I:%M %p UTC')}</small></p>
            </div>
        """

    def _create_daily_text_email(self, report_date: date, ranked_ideas: List[Dict[str, Any]]) -> str:
        """Create plain text email content for daily report."""

        high_priority = [idea for idea in ranked_ideas if idea['ai_score'] >= 75]
        medium_priority = [idea for idea in ranked_ideas if 60 <= idea['ai_score'] < 75]
        low_priority = [idea for idea in ranked_ideas if idea['ai_score'] < 60]

        text = f"""
DAILY SAAS IDEAS REPORT
{report_date.strftime('%A, %B %d, %Y')}

DAILY SUMMARY
=============
- {len(ranked_ideas)} new ideas discovered today
- {len(high_priority)} high-priority ideas (AI score ≥75)
- {len(medium_priority)} medium-priority ideas (AI score 60-74)
- {len(low_priority)} lower-priority ideas (AI score <60)

"""

        if high_priority:
            text += """
HIGH PRIORITY IDEAS (AI Score ≥75)
===================================
"""
            for idea in high_priority:
                text += self._format_daily_idea_text(idea)

        if medium_priority:
            text += """
MEDIUM PRIORITY IDEAS (AI Score 60-74)
=======================================
"""
            for idea in medium_priority:
                text += self._format_daily_idea_text(idea)

        if low_priority:
            text += """
OTHER IDEAS (AI Score <60)
==========================
"""
            for idea in low_priority:
                text += self._format_daily_idea_text(idea)

        text += """
---
Generated by SaaS Project Finder AI Backend
This daily report includes all new ideas discovered in the last 24 hours with AI analysis and ranking.
"""

        return text

    def _format_daily_idea_text(self, idea: Dict[str, Any]) -> str:
        """Format a single idea for daily text email."""

        analysis = idea.get('analysis', {})

        return f"""
{idea['title']} (AI Score: {idea['ai_score']:.0f}/100)
{'-' * 50}
{idea['description']}

Analysis Summary:
- Market Potential: {analysis.get('market_potential', 'Not analyzed')}
- AI Implementation: {analysis.get('ai_implementation_notes', 'Not analyzed')}
- Competition Level: {analysis.get('competition_analysis', 'Not analyzed')}
- Revenue Potential: {analysis.get('monetization_potential', 'Not analyzed')}

Source: {idea['source_platform'].title()} - {idea.get('source_url', 'N/A')}
Discovered: {idea['discovered_at'].strftime('%I:%M %p UTC')}

"""

    async def send_immediate_alert(self, idea: Dict[str, Any], alert_type: str = "high_potential") -> bool:
        """Send immediate alert for exceptional SaaS ideas."""

        try:
            subject = f"🚨 {alert_type.replace('_', ' ').title()} SaaS Idea Alert: {idea['title']}"

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d63384;">🚨 Immediate Alert: High Potential SaaS Idea</h2>

                <div style="border: 2px solid #d63384; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h3>{idea['title']} (Score: {idea.get('composite_score', 0):.1f}/100)</h3>
                    <p>{idea['description']}</p>

                    <p><strong>Source:</strong> {idea.get('source_platform', 'Unknown')} -
                       <a href="{idea.get('source_url', '#')}">View Original</a></p>

                    <p><strong>Why this is exceptional:</strong></p>
                    <ul>
                        <li>AI Suitability: {idea.get('scores', {}).get('ai_suitability', 0):.0f}/100</li>
                        <li>Market Potential: {idea.get('scores', {}).get('market', 0):.0f}/100</li>
                        <li>Competition Level: {idea.get('scores', {}).get('competition', 0):.0f}/100</li>
                    </ul>
                </div>

                <p><em>This alert was triggered automatically based on exceptionally high scores.</em></p>
            </body>
            </html>
            """

            text_content = f"""
IMMEDIATE ALERT: High Potential SaaS Idea

{idea['title']} (Score: {idea.get('composite_score', 0):.1f}/100)

{idea['description']}

Source: {idea.get('source_platform', 'Unknown')} - {idea.get('source_url', 'N/A')}

Why this is exceptional:
- AI Suitability: {idea.get('scores', {}).get('ai_suitability', 0):.0f}/100
- Market Potential: {idea.get('scores', {}).get('market', 0):.0f}/100
- Competition Level: {idea.get('scores', {}).get('competition', 0):.0f}/100

This alert was triggered automatically based on exceptionally high scores.
            """

            return await self._send_email(
                recipients=self.default_recipients,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

        except Exception as e:
            logger.error("Failed to send immediate alert",
                        idea_title=idea.get('title', 'Unknown'),
                        error=str(e))
            return False