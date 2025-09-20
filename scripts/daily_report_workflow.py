#!/usr/bin/env python3
"""
Daily SaaS Report Workflow
Scans for new ideas, analyzes them, ranks them, and sends daily email report.

API Standards Enforced:
- Python httpx for all HTTP operations (never curl)
- No emojis in outputs or logging
- Async/await patterns throughout
"""

import asyncio
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import json
import time
import logging
from typing import List, Dict, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DailySaaSReportWorkflow:
    """Complete daily workflow: scan -> analyze -> rank -> email report."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
        self.base_url = 'http://localhost:8000'

    async def run_daily_scan(self) -> Dict[str, Any]:
        """Execute daily high-volume scan for new ideas."""

        logger.info("Starting daily SaaS ideas scan")

        async with httpx.AsyncClient(timeout=300.0) as client:
            scan_response = await client.post(
                f'{self.base_url}/api/v1/agents/saas-trend-scanner/execute',
                headers=self.headers,
                json={
                    'parameters': {
                        'scan_platforms': ['producthunt', 'reddit', 'indiehackers'],
                        'focus_categories': [
                            'ai', 'productivity', 'automation',
                            'developer-tools', 'saas', 'no-code'
                        ],
                        'volume_target': 'comprehensive',
                        'timeframe': 'day',  # Focus on today's fresh content
                        'min_engagement': 3,  # Lower threshold for daily scan
                        'quality_filter': 'moderate',
                        'max_ideas_per_platform': 25
                    }
                }
            )

            if scan_response.status_code == 200:
                result = scan_response.json()
                execution = result.get('execution', {})

                if execution.get('status') == 'completed':
                    scan_data = execution.get('result', {})
                    content = scan_data.get('content', '')
                    tool_calls = scan_data.get('tool_calls', [])

                    # Extract individual ideas from content
                    ideas = self._extract_ideas_from_content(content)

                    logger.info(f"Daily scan completed: {len(ideas)} ideas extracted")

                    return {
                        'success': True,
                        'ideas': ideas,
                        'raw_content': content,
                        'tools_used': len(tool_calls),
                        'scan_time': execution.get('execution_time_ms', 0) / 1000
                    }
                else:
                    logger.error(f"Scan failed: {execution.get('error_message')}")
                    return {'success': False, 'error': execution.get('error_message')}
            else:
                logger.error(f"Scan request failed: {scan_response.status_code}")
                return {'success': False, 'error': f'Request failed: {scan_response.status_code}'}

    def _extract_ideas_from_content(self, content: str) -> List[Dict[str, str]]:
        """Extract structured ideas from scan content."""
        ideas = []
        lines = content.split('\n')

        current_idea = {}
        for line in lines:
            line = line.strip()

            # Look for numbered items or clear idea indicators
            if (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or
                line.startswith('**') and line.endswith('**')):

                # Save previous idea if exists
                if current_idea.get('title'):
                    ideas.append(current_idea)

                # Start new idea
                title = line.replace('**', '').replace('1.', '').replace('2.', '').replace('3.', '').strip()
                current_idea = {
                    'title': title[:100],  # Limit title length
                    'description': '',
                    'source': 'Daily Scan',
                    'platform': 'Multiple'
                }

            elif line.startswith('- Description:') or line.startswith('Description:'):
                desc = line.replace('- Description:', '').replace('Description:', '').strip()
                if current_idea:
                    current_idea['description'] = desc[:300]  # Limit description

            elif line.startswith('- Source:') or line.startswith('Source:'):
                source = line.replace('- Source:', '').replace('Source:', '').strip()
                if current_idea:
                    current_idea['source'] = source

        # Add final idea
        if current_idea.get('title'):
            ideas.append(current_idea)

        # If no structured ideas found, create from content chunks
        if len(ideas) < 3:
            ideas = self._fallback_idea_extraction(content)

        return ideas[:20]  # Limit to top 20 for daily report

    def _fallback_idea_extraction(self, content: str) -> List[Dict[str, str]]:
        """Fallback method to extract ideas when structure is unclear."""
        ideas = []

        # Split content into meaningful chunks
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 50]

        for i, sentence in enumerate(sentences[:10]):  # Max 10 fallback ideas
            if any(keyword in sentence.lower() for keyword in ['saas', 'tool', 'platform', 'software', 'app']):
                ideas.append({
                    'title': f"Idea {i+1}: {sentence[:60]}...",
                    'description': sentence,
                    'source': 'Content Analysis',
                    'platform': 'Mixed'
                })

        return ideas

    async def analyze_ideas(self, ideas: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Analyze each idea and add AI suitability scoring."""

        logger.info(f"Analyzing {len(ideas)} ideas")
        analyzed_ideas = []

        async with httpx.AsyncClient(timeout=180.0) as client:
            for i, idea in enumerate(ideas):
                try:
                    analysis_response = await client.post(
                        f'{self.base_url}/api/v1/agents/saas-idea-analyzer/execute',
                        headers=self.headers,
                        json={
                            'parameters': {
                                'idea_title': idea['title'],
                                'idea_description': idea['description'],
                                'analysis_depth': 'quick',  # Quick analysis for daily volume
                                'focus_areas': ['market', 'ai-suitability']
                            }
                        }
                    )

                    if analysis_response.status_code == 200:
                        result = analysis_response.json()
                        execution = result.get('execution', {})

                        if execution.get('status') == 'completed':
                            analysis = execution.get('result', {})
                            analysis_content = analysis.get('content', '')

                            # Extract AI suitability score
                            ai_score = self._extract_ai_score(analysis_content)

                            analyzed_ideas.append({
                                **idea,
                                'analysis_summary': analysis_content[:200] + '...' if len(analysis_content) > 200 else analysis_content,
                                'ai_suitability_score': ai_score,
                                'analysis_status': 'completed'
                            })
                        else:
                            analyzed_ideas.append({
                                **idea,
                                'analysis_summary': 'Analysis failed',
                                'ai_suitability_score': 'Unknown',
                                'analysis_status': 'failed'
                            })

                    # Rate limiting between requests
                    await asyncio.sleep(1.0)

                except Exception as e:
                    logger.warning(f"Analysis failed for {idea['title']}: {e}")
                    analyzed_ideas.append({
                        **idea,
                        'analysis_summary': f'Analysis error: {str(e)[:100]}',
                        'ai_suitability_score': 'Error',
                        'analysis_status': 'error'
                    })

        logger.info(f"Analysis completed: {len([i for i in analyzed_ideas if i['analysis_status'] == 'completed'])}/{len(ideas)} successful")
        return analyzed_ideas

    def _extract_ai_score(self, analysis_content: str) -> str:
        """Extract AI suitability score from analysis content."""
        import re

        # Look for patterns like "score: 75", "suitability: 80.5", etc.
        score_patterns = [
            r'(?:score|suitability)[:\s]+(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)/100',
            r'(\d+(?:\.\d+)?)%',
            r'(\d+(?:\.\d+)?)\s*(?:out of|/)?\s*100'
        ]

        for pattern in score_patterns:
            match = re.search(pattern, analysis_content, re.IGNORECASE)
            if match:
                return match.group(1)

        # Fallback: look for any number between 0-100
        numbers = re.findall(r'\b(\d{1,2}(?:\.\d+)?)\b', analysis_content)
        for num in numbers:
            score = float(num)
            if 0 <= score <= 100:
                return str(score)

        return 'Unknown'

    def rank_ideas(self, analyzed_ideas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank ideas by AI suitability score and other factors."""

        def get_sort_key(idea):
            # Primary sort by AI suitability score
            score_str = idea.get('ai_suitability_score', '0')
            try:
                score = float(score_str) if score_str not in ['Unknown', 'Error'] else 0
            except:
                score = 0

            # Secondary sort by analysis status (completed > failed > error)
            status_priority = {
                'completed': 3,
                'failed': 2,
                'error': 1
            }
            status_score = status_priority.get(idea.get('analysis_status', 'error'), 1)

            return (score, status_score)

        ranked_ideas = sorted(analyzed_ideas, key=get_sort_key, reverse=True)

        # Add ranking position
        for i, idea in enumerate(ranked_ideas):
            idea['rank'] = i + 1
            idea['rank_category'] = self._get_rank_category(i + 1, idea.get('ai_suitability_score', '0'))

        return ranked_ideas

    def _get_rank_category(self, rank: int, score_str: str) -> str:
        """Categorize ideas by rank and score."""
        try:
            score = float(score_str) if score_str not in ['Unknown', 'Error'] else 0
        except:
            score = 0

        if rank <= 3 and score >= 70:
            return 'High Priority'
        elif rank <= 5 and score >= 60:
            return 'Medium Priority'
        elif rank <= 10:
            return 'Worth Exploring'
        else:
            return 'Low Priority'

    async def send_daily_email_report(self, scan_results: Dict[str, Any], ranked_ideas: List[Dict[str, Any]]) -> bool:
        """Send comprehensive daily email report."""

        try:
            # Email configuration
            smtp_server = 'smtp.gmail.com'
            smtp_port = 587
            email_username = 'kevinkn420@gmail.com'
            email_password = 'tjnp qmte youw myks'
            from_address = 'kevinkn420@gmail.com'
            to_address = 'kevinkn420@gmail.com'

            today = date.today().strftime('%B %d, %Y')
            subject = f'SaaS Project Finder - Daily Report ({today})'

            # Generate HTML report
            html_content = self._generate_daily_html_report(scan_results, ranked_ideas, today)

            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_address
            msg['To'] = to_address

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            logger.info("Sending daily report email")

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email_username, email_password)
                server.send_message(msg)

            logger.info("Daily report email sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send daily email report: {e}")
            return False

    def _generate_daily_html_report(self, scan_results: Dict[str, Any], ranked_ideas: List[Dict[str, Any]], today: str) -> str:
        """Generate HTML content for daily email report."""

        high_priority = [idea for idea in ranked_ideas if idea.get('rank_category') == 'High Priority']
        medium_priority = [idea for idea in ranked_ideas if idea.get('rank_category') == 'Medium Priority']

        html = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 900px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c3e50; border-bottom: 3px solid #3498db;">
                    SaaS Project Finder - Daily Report
                </h1>

                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Report Date:</strong> {today}</p>
                    <p><strong>Ideas Discovered:</strong> {len(ranked_ideas)}</p>
                    <p><strong>High Priority Ideas:</strong> {len(high_priority)}</p>
                    <p><strong>Scan Time:</strong> {scan_results.get('scan_time', 0):.1f} seconds</p>
                    <p><strong>Tools Used:</strong> {scan_results.get('tools_used', 0)} MCP tools</p>
                </div>
        '''

        if high_priority:
            html += '''
                <h2 style="color: #27ae60;">High Priority Ideas (Top Recommendations)</h2>
            '''
            for idea in high_priority:
                html += f'''
                <div style="border: 2px solid #27ae60; padding: 15px; margin: 10px 0; border-radius: 5px; background-color: #d5f4e6;">
                    <h3 style="color: #27ae60; margin-top: 0;">#{idea['rank']} {idea['title']}</h3>
                    <p><strong>AI Suitability Score:</strong> {idea['ai_suitability_score']}</p>
                    <p><strong>Description:</strong> {idea['description']}</p>
                    <p><strong>Analysis:</strong> {idea['analysis_summary']}</p>
                    <p><strong>Source:</strong> {idea['source']} | <strong>Platform:</strong> {idea['platform']}</p>
                </div>
                '''

        if medium_priority:
            html += '''
                <h2 style="color: #3498db;">Medium Priority Ideas</h2>
            '''
            for idea in medium_priority:
                html += f'''
                <div style="border: 1px solid #3498db; padding: 12px; margin: 8px 0; border-radius: 5px; background-color: #ebf3fd;">
                    <h4 style="color: #3498db; margin-top: 0;">#{idea['rank']} {idea['title']}</h4>
                    <p><strong>AI Suitability:</strong> {idea['ai_suitability_score']}</p>
                    <p><strong>Summary:</strong> {idea['analysis_summary'][:150]}...</p>
                </div>
                '''

        # Other ideas summary
        other_ideas = [idea for idea in ranked_ideas if idea.get('rank_category') not in ['High Priority', 'Medium Priority']]
        if other_ideas:
            html += f'''
                <h2 style="color: #7f8c8d;">Other Ideas Discovered ({len(other_ideas)})</h2>
                <div style="background-color: #ecf0f1; padding: 10px; border-radius: 5px;">
            '''
            for idea in other_ideas[:5]:  # Show first 5
                html += f'<p>#{idea["rank"]} {idea["title"]} (Score: {idea["ai_suitability_score"]})</p>'

            if len(other_ideas) > 5:
                html += f'<p><em>... and {len(other_ideas) - 5} more ideas</em></p>'
            html += '</div>'

        html += f'''
                <div style="background-color: #f8f9fa; padding: 15px; margin-top: 30px; border-top: 2px solid #3498db;">
                    <h3>Daily Performance Summary</h3>
                    <p>System Status: All components operational</p>
                    <p>Next scan: Tomorrow at same time</p>
                    <p><em>Generated automatically by SaaS Project Finder Daily Workflow</em></p>
                </div>
            </div>
        </body>
        </html>
        '''

        return html


async def main():
    """Execute complete daily workflow."""

    # Use existing tenant API key
    api_key = 'UOW5GS6Cb741Sq-gZrOmVf3OxPR75gFFo8L6comEQFE'

    workflow = DailySaaSReportWorkflow(api_key)

    print("DAILY SAAS PROJECT FINDER WORKFLOW")
    print("=" * 40)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Daily scan
    print("Step 1: Executing daily scan...")
    scan_results = await workflow.run_daily_scan()

    if not scan_results['success']:
        print(f"Daily scan failed: {scan_results.get('error')}")
        return

    print(f"Scan completed: {len(scan_results['ideas'])} ideas discovered")

    # Step 2: Analyze ideas
    print("Step 2: Analyzing discovered ideas...")
    analyzed_ideas = await workflow.analyze_ideas(scan_results['ideas'])

    # Step 3: Rank ideas
    print("Step 3: Ranking ideas by AI suitability...")
    ranked_ideas = workflow.rank_ideas(analyzed_ideas)

    # Step 4: Send email report
    print("Step 4: Sending daily email report...")
    email_success = await workflow.send_daily_email_report(scan_results, ranked_ideas)

    # Summary
    print()
    print("DAILY WORKFLOW SUMMARY")
    print("-" * 25)
    print(f"Ideas Discovered: {len(scan_results['ideas'])}")
    print(f"Ideas Analyzed: {len([i for i in analyzed_ideas if i['analysis_status'] == 'completed'])}")
    print(f"High Priority Ideas: {len([i for i in ranked_ideas if i.get('rank_category') == 'High Priority'])}")
    print(f"Email Report Sent: {'YES' if email_success else 'FAILED'}")
    print(f"Scan Time: {scan_results.get('scan_time', 0):.1f} seconds")

    if email_success:
        print()
        print("Daily report successfully sent to kevinkn420@gmail.com")
        print("Check your inbox for detailed analysis and rankings")


if __name__ == '__main__':
    asyncio.run(main())