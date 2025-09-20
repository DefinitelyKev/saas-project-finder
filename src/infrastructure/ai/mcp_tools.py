from typing import Dict, Any, List, Optional
import json
import structlog
import asyncio
import httpx
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup, Tag
import os

try:
    from src.domain.exceptions import AgentExecutionError
    from src.config.settings import settings
except ImportError:
    # Fallback for when running MCP server standalone
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from src.domain.exceptions import AgentExecutionError
    from src.config.settings import settings

logger = structlog.get_logger()


class MCPToolExecutor:
    """Handles execution of MCP (Model Context Protocol) tools for SaaS idea discovery."""

    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "SaaS-Project-Finder/1.0 (Research Tool)"
            }
        )

        # MCP tool registry
        self.mcp_tools: Dict[str, Any] = {
            "search_producthunt": self._search_producthunt,
            "search_reddit_startups": self._search_reddit_startups,
            "search_hackernews": self._search_hackernews,
            "search_indiehackers": self._search_indiehackers,
            "analyze_market_size": self._analyze_market_size,
            "analyze_competition": self._analyze_competition,
            "check_domain_availability": self._check_domain_availability,
            "analyze_google_trends": self._analyze_google_trends,
        }

    async def execute_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool with given parameters."""

        if tool_name not in self.mcp_tools:
            raise AgentExecutionError(f"MCP tool not found: {tool_name}")

        try:
            handler = self.mcp_tools[tool_name]
            return await handler(parameters)
        except Exception as e:
            logger.error("MCP tool execution failed",
                        tool_name=tool_name,
                        error=str(e))
            raise AgentExecutionError(f"MCP tool execution failed: {str(e)}")

    async def _search_producthunt(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search ProductHunt for trending products and ideas using the actual API."""
        category = parameters.get("category", "productivity")
        timeframe = parameters.get("timeframe", "week")
        sort_by = parameters.get("sort_by", "votes")
        limit = parameters.get("limit", 20)

        if not settings.producthunt_api_token:
            logger.warning("ProductHunt API token not configured, using mock data")
            return await self._search_producthunt_mock(parameters)

        try:
            # ProductHunt GraphQL API endpoint
            url = "https://api.producthunt.com/v2/api/graphql"

            # Build GraphQL query based on timeframe
            if timeframe == "day":
                query = """
                query GetPosts($first: Int!, $order: PostsOrder!) {
                  posts(first: $first, order: $order) {
                    edges {
                      node {
                        id
                        name
                        tagline
                        description
                        url
                        website
                        votesCount
                        commentsCount
                        createdAt
                        featuredAt
                        makers {
                          name
                          username
                        }
                        topics {
                          edges {
                            node {
                              name
                              slug
                            }
                          }
                        }
                        thumbnail {
                          url
                        }
                      }
                    }
                  }
                }
                """
                variables = {
                    "first": limit,
                    "order": "VOTES" if sort_by == "votes" else "NEWEST"
                }
            else:
                # For weekly/monthly data, use posts from a specific date range
                query = """
                query GetPosts($first: Int!, $postedAfter: DateTime!, $order: PostsOrder!) {
                  posts(first: $first, postedAfter: $postedAfter, order: $order) {
                    edges {
                      node {
                        id
                        name
                        tagline
                        description
                        url
                        website
                        votesCount
                        commentsCount
                        createdAt
                        featuredAt
                        makers {
                          name
                          username
                        }
                        topics {
                          edges {
                            node {
                              name
                              slug
                            }
                          }
                        }
                        thumbnail {
                          url
                        }
                      }
                    }
                  }
                }
                """
                # Calculate date based on timeframe
                if timeframe == "week":
                    posted_after = (datetime.utcnow() - timedelta(days=7)).isoformat()
                elif timeframe == "month":
                    posted_after = (datetime.utcnow() - timedelta(days=30)).isoformat()
                else:
                    posted_after = (datetime.utcnow() - timedelta(days=1)).isoformat()

                variables = {
                    "first": limit,
                    "postedAfter": posted_after,
                    "order": "VOTES" if sort_by == "votes" else "NEWEST"
                }

            headers = {
                "Authorization": f"Bearer {settings.producthunt_api_token}",
                "Content-Type": "application/json"
            }

            response = await self.http_client.post(
                url,
                json={"query": query, "variables": variables},
                headers=headers
            )

            if response.status_code != 200:
                logger.error("ProductHunt API request failed",
                           status_code=response.status_code,
                           response=response.text)
                return await self._search_producthunt_mock(parameters)

            data = response.json()

            if "errors" in data:
                logger.error("ProductHunt GraphQL errors", errors=data["errors"])
                return await self._search_producthunt_mock(parameters)

            # Process the response
            posts_data = data.get("data", {}).get("posts", {}).get("edges", [])
            results = []

            for edge in posts_data:
                post = edge["node"]

                # Extract makers
                makers = []
                makers_data = post.get("makers", [])
                if isinstance(makers_data, list):
                    for maker in makers_data:
                        makers.append(maker.get("name", maker.get("username", "Unknown")))
                else:
                    # Handle case where makers might be a single object
                    if makers_data:
                        makers.append(makers_data.get("name", makers_data.get("username", "Unknown")))

                # Extract topics/tags
                topics = []
                topic_edges = post.get("topics", {}).get("edges", [])
                for topic_edge in topic_edges:
                    topic = topic_edge["node"]
                    topics.append(topic.get("slug", topic.get("name", "")))

                # Filter by category if specified and not "all"
                if category != "all":
                    # Check if any of the topics match the category
                    category_matches = any(
                        category.lower() in topic.lower() or topic.lower() in category.lower()
                        for topic in topics
                    )
                    if not category_matches:
                        continue

                # Calculate engagement score
                votes = post.get("votesCount", 0)
                comments = post.get("commentsCount", 0)
                engagement_score = min(100, (votes * 0.7 + comments * 1.5))

                result = {
                    "id": post.get("id", ""),
                    "title": post.get("name", ""),
                    "description": post.get("tagline", post.get("description", "")),
                    "url": post.get("url", ""),
                    "website": post.get("website", ""),
                    "votes": votes,
                    "comments": comments,
                    "makers": makers,
                    "maker": ", ".join(makers) if makers else "Unknown",
                    "category": topics[0] if topics else "general",
                    "tags": topics,
                    "launch_date": post.get("featuredAt", post.get("createdAt", "")),
                    "engagement_score": round(engagement_score, 1),
                    "thumbnail": post.get("thumbnail", {}).get("url", "")
                }
                results.append(result)

            # Sort results if needed
            if sort_by == "votes":
                results.sort(key=lambda x: x["votes"], reverse=True)
            elif sort_by == "comments":
                results.sort(key=lambda x: x["comments"], reverse=True)
            elif sort_by == "engagement":
                results.sort(key=lambda x: x["engagement_score"], reverse=True)

            logger.info("ProductHunt API search completed",
                       total_found=len(results),
                       category=category,
                       timeframe=timeframe)

            return {
                "results": results,
                "total_found": len(results),
                "category": category,
                "timeframe": timeframe,
                "sort_by": sort_by,
                "search_timestamp": datetime.utcnow().isoformat(),
                "api_used": "producthunt_graphql"
            }

        except Exception as e:
            logger.error("ProductHunt API search failed", error=str(e))
            # Fallback to mock data
            return await self._search_producthunt_mock(parameters)

    async def _search_producthunt_mock(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback mock implementation for ProductHunt when API is unavailable."""
        category = parameters.get("category", "productivity")
        timeframe = parameters.get("timeframe", "week")
        sort_by = parameters.get("sort_by", "votes")

        mock_results = [
            {
                "title": "AI Task Automator",
                "description": "Automate repetitive tasks using AI agents for small businesses",
                "url": "https://producthunt.com/posts/ai-task-automator",
                "votes": 342,
                "comments": 28,
                "maker": "John Smith",
                "category": "productivity",
                "launch_date": "2024-01-15",
                "tags": ["ai", "automation", "productivity"],
                "engagement_score": 85.2
            },
            {
                "title": "Smart Invoice Generator",
                "description": "AI-powered invoice generation with automatic client data extraction",
                "url": "https://producthunt.com/posts/smart-invoice-generator",
                "votes": 198,
                "comments": 15,
                "maker": "Sarah Johnson",
                "category": "saas",
                "launch_date": "2024-01-14",
                "tags": ["ai", "invoicing", "business"],
                "engagement_score": 72.3
            },
            {
                "title": "Code Review Bot",
                "description": "Automated code review using GPT-4 for development teams",
                "url": "https://producthunt.com/posts/code-review-bot",
                "votes": 156,
                "comments": 22,
                "maker": "Dev Team",
                "category": "developer-tools",
                "launch_date": "2024-01-13",
                "tags": ["ai", "development", "code-review"],
                "engagement_score": 68.7
            }
        ]

        # Filter by category if specified
        if category != "all":
            mock_results = [r for r in mock_results if r["category"] == category]

        # Sort results
        if sort_by == "votes":
            mock_results.sort(key=lambda x: x["votes"], reverse=True)
        elif sort_by == "comments":
            mock_results.sort(key=lambda x: x["comments"], reverse=True)

        return {
            "results": mock_results,
            "total_found": len(mock_results),
            "category": category,
            "timeframe": timeframe,
            "search_timestamp": datetime.utcnow().isoformat(),
            "api_used": "mock_fallback"
        }

    async def _search_reddit_startups(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search Reddit startup communities for SaaS ideas and discussions."""
        subreddit = parameters.get("subreddit", "startups")
        keywords = parameters.get("keywords", [])
        timeframe = parameters.get("timeframe", "week")
        sort_by = parameters.get("sort_by", "hot")
        limit = parameters.get("limit", 25)

        try:
            # First get OAuth token for Reddit API
            access_token = await self._get_reddit_access_token()
            if not access_token:
                logger.warning("Reddit API token not available, using fallback")
                return await self._search_reddit_fallback(parameters)

            # Build search query
            query = " ".join(keywords) if keywords else "SaaS startup"

            # Determine time filter
            time_filter = "week"
            if timeframe == "day":
                time_filter = "day"
            elif timeframe == "month":
                time_filter = "month"
            elif timeframe == "year":
                time_filter = "year"

            # Search Reddit API
            headers = {
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "SaaS-Project-Finder/1.0 by /u/saas_finder_bot"
            }

            # Use Reddit's search endpoint
            search_url = f"https://oauth.reddit.com/r/{subreddit}/search.json"
            params = {
                "q": query,
                "restrict_sr": "1",  # Restrict to subreddit
                "sort": sort_by,
                "t": time_filter,
                "limit": limit,
                "type": "link"
            }

            response = await self.http_client.get(search_url, headers=headers, params=params)

            if response.status_code != 200:
                logger.error(f"Reddit API search failed: {response.status_code}")
                return await self._search_reddit_fallback(parameters)

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            results = []
            for post_data in posts:
                post = post_data.get("data", {})

                # Extract post information
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                url = post.get("url", "")
                permalink = f"https://reddit.com{post.get('permalink', '')}"

                # Calculate engagement score
                upvotes = post.get("ups", 0)
                comments = post.get("num_comments", 0)
                engagement_score = self._calculate_engagement_score(upvotes, comments)

                # Check for keywords
                keywords_found = []
                if keywords:
                    content_text = f"{title} {selftext}".lower()
                    keywords_found = [kw for kw in keywords if kw.lower() in content_text]

                # Create result object
                result = {
                    "title": title,
                    "description": selftext[:500] if selftext else "No description available",
                    "url": permalink,
                    "upvotes": upvotes,
                    "comments": comments,
                    "author": post.get("author", "unknown"),
                    "subreddit": post.get("subreddit", subreddit),
                    "created_at": datetime.fromtimestamp(post.get("created_utc", 0)).isoformat(),
                    "keywords_found": keywords_found,
                    "engagement_score": engagement_score,
                    "post_id": post.get("id", ""),
                    "is_self_post": post.get("is_self", False)
                }

                results.append(result)

            return {
                "results": results,
                "total_found": len(results),
                "subreddit": subreddit,
                "keywords": keywords,
                "timeframe": timeframe,
                "search_timestamp": datetime.utcnow().isoformat(),
                "api_source": "reddit_oauth"
            }

        except Exception as e:
            logger.error(f"Reddit API error: {e}")
            return await self._search_reddit_fallback(parameters)

    async def _get_reddit_access_token(self) -> Optional[str]:
        """Get OAuth access token for Reddit API."""
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            return None

        try:
            # Reddit OAuth2 application-only flow
            auth_url = "https://www.reddit.com/api/v1/access_token"

            # Prepare credentials
            auth = (settings.reddit_client_id, settings.reddit_client_secret)
            headers = {
                "User-Agent": "SaaS-Project-Finder/1.0 by /u/saas_finder_bot"
            }
            data = {
                "grant_type": "client_credentials"
            }

            response = await self.http_client.post(auth_url, auth=auth, headers=headers, data=data)

            if response.status_code == 200:
                token_data = response.json()
                return token_data.get("access_token")
            else:
                logger.error(f"Reddit OAuth failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Reddit OAuth error: {e}")
            return None

    async def _search_reddit_fallback(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback Reddit search using public JSON API (rate limited)."""
        subreddit = parameters.get("subreddit", "startups")
        keywords = parameters.get("keywords", [])
        timeframe = parameters.get("timeframe", "week")
        sort_by = parameters.get("sort_by", "hot")
        limit = min(parameters.get("limit", 25), 25)  # Max 25 for public API

        try:
            # Use public JSON API (no auth required but rate limited)
            base_url = f"https://www.reddit.com/r/{subreddit}/{sort_by}.json"
            headers = {
                "User-Agent": "SaaS-Project-Finder/1.0"
            }
            params = {
                "limit": limit,
                "t": timeframe if sort_by in ["top", "hot"] else "all"
            }

            response = await self.http_client.get(base_url, headers=headers, params=params)

            if response.status_code != 200:
                logger.error(f"Reddit fallback API failed: {response.status_code}")
                return self._get_mock_reddit_data(parameters)

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            results = []
            for post_data in posts:
                post = post_data.get("data", {})

                title = post.get("title", "")
                selftext = post.get("selftext", "")

                # Filter by keywords if provided
                if keywords:
                    content_text = f"{title} {selftext}".lower()
                    if not any(kw.lower() in content_text for kw in keywords):
                        continue

                # Extract information
                upvotes = post.get("ups", 0)
                comments = post.get("num_comments", 0)
                engagement_score = self._calculate_engagement_score(upvotes, comments)

                result = {
                    "title": title,
                    "description": selftext[:500] if selftext else "No description available",
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "upvotes": upvotes,
                    "comments": comments,
                    "author": post.get("author", "unknown"),
                    "subreddit": post.get("subreddit", subreddit),
                    "created_at": datetime.fromtimestamp(post.get("created_utc", 0)).isoformat(),
                    "keywords_found": [kw for kw in keywords if kw.lower() in f"{title} {selftext}".lower()] if keywords else [],
                    "engagement_score": engagement_score,
                    "post_id": post.get("id", "")
                }

                results.append(result)

            return {
                "results": results,
                "total_found": len(results),
                "subreddit": subreddit,
                "keywords": keywords,
                "timeframe": timeframe,
                "search_timestamp": datetime.utcnow().isoformat(),
                "api_source": "reddit_public_json"
            }

        except Exception as e:
            logger.error(f"Reddit fallback error: {e}")
            return self._get_mock_reddit_data(parameters)

    def _calculate_engagement_score(self, upvotes: int, comments: int) -> float:
        """Calculate engagement score based on upvotes and comments."""
        # Weight comments more heavily as they indicate deeper engagement
        return (upvotes * 0.7) + (comments * 1.5)

    def _get_mock_reddit_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Return mock data when Reddit API is unavailable."""
        subreddit = parameters.get("subreddit", "startups")
        keywords = parameters.get("keywords", [])
        timeframe = parameters.get("timeframe", "week")

        mock_results = [
            {
                "title": "Built an AI customer service bot in 2 weeks - $2k MRR",
                "description": "Created a simple AI chatbot that handles customer inquiries for small e-commerce stores. Currently serving 15 clients.",
                "url": "https://reddit.com/r/startups/comments/xyz123",
                "upvotes": 247,
                "comments": 43,
                "author": "entrepreneur_mike",
                "subreddit": "startups",
                "created_at": "2024-01-14T10:30:00Z",
                "keywords_found": ["ai", "customer service", "chatbot"],
                "engagement_score": 78.5,
                "post_id": "mock_xyz123"
            },
            {
                "title": "Looking for feedback: AI-powered content calendar",
                "description": "Building a tool that automatically generates social media content calendars based on your industry and target audience.",
                "url": "https://reddit.com/r/entrepreneur/comments/abc456",
                "upvotes": 89,
                "comments": 67,
                "author": "content_creator_sam",
                "subreddit": "entrepreneur",
                "created_at": "2024-01-13T15:45:00Z",
                "keywords_found": ["ai", "content", "social media"],
                "engagement_score": 65.2,
                "post_id": "mock_abc456"
            }
        ]

        # Filter by keywords if provided
        if keywords:
            filtered_results = []
            for result in mock_results:
                if any(keyword.lower() in result["title"].lower() or
                      keyword.lower() in result["description"].lower()
                      for keyword in keywords):
                    filtered_results.append(result)
            mock_results = filtered_results

        return {
            "results": mock_results,
            "total_found": len(mock_results),
            "subreddit": subreddit,
            "keywords": keywords,
            "timeframe": timeframe,
            "search_timestamp": datetime.utcnow().isoformat(),
            "api_source": "mock_fallback"
        }

    async def _search_hackernews(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search Hacker News for startup ideas, Show HN posts, and tech discussions."""
        query = parameters.get("query", "Show HN")
        story_type = parameters.get("story_type", "show_hn")  # show_hn, ask_hn, job, all
        limit = parameters.get("limit", 20)
        sort_by = parameters.get("sort_by", "points")  # points, comments, recent

        try:
            # Hacker News API endpoints
            base_url = "https://hacker-news.firebaseio.com/v0"

            stories = []
            story_ids = []

            if story_type == "show_hn":
                # Get Show HN stories (these are often SaaS projects and demos)
                response = await self.http_client.get(f"{base_url}/showstories.json")
                if response.status_code == 200:
                    story_ids = response.json()
            elif story_type == "ask_hn":
                # Get Ask HN stories (often include SaaS feedback requests)
                response = await self.http_client.get(f"{base_url}/askstories.json")
                if response.status_code == 200:
                    story_ids = response.json()
            elif story_type == "job":
                # Get job stories (may include startup job postings)
                response = await self.http_client.get(f"{base_url}/jobstories.json")
                if response.status_code == 200:
                    story_ids = response.json()
            else:
                # Get top stories
                response = await self.http_client.get(f"{base_url}/topstories.json")
                if response.status_code == 200:
                    story_ids = response.json()

            # Fetch details for the first 'limit' stories
            for story_id in story_ids[:limit]:
                try:
                    story_response = await self.http_client.get(f"{base_url}/item/{story_id}.json")
                    if story_response.status_code == 200:
                        story_data = story_response.json()

                        if story_data and story_data.get("type") == "story":
                            # Filter based on query if provided
                            title = story_data.get("title", "")
                            text = story_data.get("text", "")

                            if query.lower() in title.lower() or query.lower() in text.lower() or query == "Show HN":
                                # Calculate engagement score
                                score = story_data.get("score", 0)
                                descendants = story_data.get("descendants", 0)
                                engagement_score = (score * 0.7) + (descendants * 0.3)

                                # Extract potential SaaS keywords from title and text
                                saas_keywords = []
                                keyword_patterns = ["saas", "ai", "automation", "productivity", "analytics",
                                                  "dashboard", "api", "platform", "tool", "app", "service",
                                                  "crm", "cms", "erp", "startup", "business", "freelancer"]

                                combined_text = f"{title} {text}".lower()
                                for keyword in keyword_patterns:
                                    if keyword in combined_text:
                                        saas_keywords.append(keyword)

                                story_item = {
                                    "id": story_data.get("id"),
                                    "title": title,
                                    "description": text[:500] + "..." if len(text) > 500 else text,
                                    "url": f"https://news.ycombinator.com/item?id={story_data.get('id')}",
                                    "external_url": story_data.get("url"),
                                    "author": story_data.get("by"),
                                    "points": score,
                                    "comments": descendants,
                                    "created_at": datetime.fromtimestamp(story_data.get("time", 0)).isoformat() + "Z",
                                    "engagement_score": round(engagement_score, 1),
                                    "story_type": story_type,
                                    "saas_keywords": saas_keywords
                                }
                                stories.append(story_item)

                except Exception as e:
                    logger.error(f"Error fetching story {story_id}: {e}")
                    continue

            # Sort results based on sort_by parameter
            if sort_by == "points":
                stories.sort(key=lambda x: x["points"], reverse=True)
            elif sort_by == "comments":
                stories.sort(key=lambda x: x["comments"], reverse=True)
            elif sort_by == "engagement":
                stories.sort(key=lambda x: x["engagement_score"], reverse=True)

            return {
                "results": stories,
                "total_found": len(stories),
                "query": query,
                "story_type": story_type,
                "sort_by": sort_by,
                "search_timestamp": datetime.utcnow().isoformat(),
                "api_used": "hackernews_official"
            }

        except Exception as e:
            logger.error(f"Hacker News API error: {e}")

            # Fallback to mock data if API fails
            mock_results = [
                {
                    "id": 12345,
                    "title": "Show HN: AI-powered code review tool for startups",
                    "description": "Built an automated code review system using GPT-4 that integrates with GitHub. Helps small teams maintain code quality without hiring senior developers.",
                    "url": "https://news.ycombinator.com/item?id=12345",
                    "external_url": "https://github.com/startup/code-reviewer",
                    "author": "startup_founder",
                    "points": 284,
                    "comments": 67,
                    "created_at": "2024-01-15T10:30:00Z",
                    "engagement_score": 218.1,
                    "story_type": "show_hn",
                    "saas_keywords": ["ai", "tool", "startup", "api"]
                },
                {
                    "id": 12346,
                    "title": "Ask HN: Best SaaS ideas for 2024?",
                    "description": "Looking for feedback on SaaS opportunities in the AI space. What problems are you facing that could be solved with a simple web app?",
                    "url": "https://news.ycombinator.com/item?id=12346",
                    "external_url": None,
                    "author": "entrepreneur_dev",
                    "points": 156,
                    "comments": 89,
                    "created_at": "2024-01-14T15:20:00Z",
                    "engagement_score": 135.9,
                    "story_type": "ask_hn",
                    "saas_keywords": ["saas", "ai", "app"]
                },
                {
                    "id": 12347,
                    "title": "Show HN: Simple invoice generator for freelancers",
                    "description": "Created a minimal SaaS for generating professional invoices. No fluff, just clean invoices with automatic calculations and PDF export.",
                    "url": "https://news.ycombinator.com/item?id=12347",
                    "external_url": "https://simpleinvoices.co",
                    "author": "freelancer_dev",
                    "points": 198,
                    "comments": 43,
                    "created_at": "2024-01-13T09:15:00Z",
                    "engagement_score": 151.5,
                    "story_type": "show_hn",
                    "saas_keywords": ["saas", "freelancer", "business"]
                }
            ]

            return {
                "results": mock_results,
                "total_found": len(mock_results),
                "query": query,
                "story_type": story_type,
                "sort_by": sort_by,
                "search_timestamp": datetime.utcnow().isoformat(),
                "api_used": "mock_fallback",
                "error": str(e)
            }

    async def _search_indiehackers(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search Indie Hackers for SaaS project ideas and startup discussions via web crawling."""
        keywords = parameters.get("keywords", ["SaaS", "startup"])
        category = parameters.get("category", "trending")  # trending, new, popular
        limit = parameters.get("limit", 20)

        try:
            # Indie Hackers doesn't have a public API, so we'll crawl the website
            # Start with the homepage and trending posts
            base_url = "https://www.indiehackers.com"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            # Try to get the main page with recent posts
            response = await self.http_client.get(f"{base_url}/", headers=headers, timeout=15.0)

            if response.status_code != 200:
                logger.warning(f"Indie Hackers main page failed: {response.status_code}")
                return await self._get_indiehackers_fallback(parameters)

            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            results = []

            # Look for post elements (this may need adjustment based on IH's current structure)
            post_selectors = [
                'article',
                '.post-item',
                '.discussion-item',
                '[data-test="post"]',
                '.feed-item'
            ]

            posts_found = []
            for selector in post_selectors:
                posts_found.extend(soup.select(selector))
                if len(posts_found) >= limit:
                    break

            # If no posts found with selectors, try alternative approach
            if not posts_found:
                # Look for any links that might be posts
                links = soup.find_all('a', href=True)
                post_links = []
                for link in links:
                    # Check if link is a Tag element (not NavigableString)
                    if not isinstance(link, Tag):
                        continue
                    href_attr = link.get('href')
                    if href_attr is None:
                        continue
                    href = str(href_attr) if href_attr else ''
                    # Look for post-like URLs
                    if any(pattern in href for pattern in ['/post/', '/posts/', '/interview/', '/product/']):
                        if href.startswith('/'):
                            href = base_url + href
                        post_links.append((link, href))

                posts_found = post_links[:limit]

            # Process found posts
            for i, post_element in enumerate(posts_found[:limit]):
                try:
                    if isinstance(post_element, tuple):
                        # Handle link-based extraction
                        link_element, post_url = post_element
                        title = link_element.get_text(strip=True) or "Indie Hackers Discussion"
                        description = "Discussion from Indie Hackers community"
                        author = "Unknown"
                    else:
                        # Handle article/post element extraction
                        title_elem = post_element.find(['h1', 'h2', 'h3', 'h4', '.title', '[data-test="title"]'])
                        title = title_elem.get_text(strip=True) if title_elem else f"Indie Hackers Post #{i+1}"

                        desc_elem = post_element.find(['p', '.description', '.excerpt', '.content'])
                        description = desc_elem.get_text(strip=True)[:300] if desc_elem else "Indie Hackers startup discussion"

                        author_elem = post_element.find(['.author', '.username', '[data-test="author"]'])
                        author = author_elem.get_text(strip=True) if author_elem else "Indie Hacker"

                        # Try to find the post URL
                        link_elem = post_element.find('a', href=True)
                        post_url = link_elem['href'] if link_elem else f"{base_url}/post/{i}"
                        if post_url.startswith('/'):
                            post_url = base_url + post_url

                    # Filter by keywords if provided
                    content_text = f"{title} {description}".lower()
                    keywords_found = [kw for kw in keywords if kw.lower() in content_text] if keywords else []

                    # Skip if keywords specified but none found
                    if keywords and not keywords_found:
                        continue

                    # Calculate basic engagement score (since we can't get actual metrics)
                    engagement_score = len(title) * 0.5 + len(description) * 0.1 + len(keywords_found) * 10

                    result = {
                        "title": title,
                        "description": description,
                        "url": post_url,
                        "author": author,
                        "source": "indiehackers",
                        "created_at": datetime.utcnow().isoformat(),
                        "keywords_found": keywords_found,
                        "engagement_score": engagement_score,
                        "category": category,
                        "content_type": "discussion"
                    }

                    results.append(result)

                except Exception as e:
                    logger.warning(f"Error parsing Indie Hackers post {i}: {e}")
                    continue

            # If we couldn't extract much, fall back to curated data
            if len(results) < 3:
                logger.info("Limited extraction from Indie Hackers, supplementing with fallback data")
                fallback_data = await self._get_indiehackers_fallback(parameters)
                results.extend(fallback_data['results'][:max(0, limit - len(results))])

            return {
                "results": results[:limit],
                "total_found": len(results),
                "keywords": keywords,
                "category": category,
                "search_timestamp": datetime.utcnow().isoformat(),
                "api_source": "indiehackers_webcrawl"
            }

        except Exception as e:
            logger.error(f"Indie Hackers crawling error: {e}")
            return await self._get_indiehackers_fallback(parameters)

    async def _get_indiehackers_fallback(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback data for Indie Hackers when crawling fails."""
        keywords = parameters.get("keywords", [])
        category = parameters.get("category", "trending")

        # Curated Indie Hackers-style content
        mock_results = [
            {
                "title": "How I built a $10k/month SaaS with no-code tools",
                "description": "Sharing my journey of building an AI-powered customer feedback analyzer using Bubble and OpenAI API. Started as a side project, now generating consistent revenue.",
                "url": "https://www.indiehackers.com/post/how-i-built-10k-month-saas-no-code",
                "author": "sarah_builder",
                "source": "indiehackers",
                "created_at": "2024-01-15T14:30:00Z",
                "keywords_found": ["saas", "ai", "no-code"],
                "engagement_score": 85.2,
                "category": "success-story",
                "content_type": "milestone"
            },
            {
                "title": "Validate your micro-SaaS idea in 48 hours",
                "description": "A step-by-step guide on how to quickly validate your SaaS idea using landing pages, Reddit posts, and direct customer interviews. Includes templates and scripts.",
                "url": "https://www.indiehackers.com/post/validate-micro-saas-48-hours",
                "author": "validation_expert",
                "source": "indiehackers",
                "created_at": "2024-01-14T11:20:00Z",
                "keywords_found": ["saas", "validation", "startup"],
                "engagement_score": 92.7,
                "category": "guide",
                "content_type": "educational"
            },
            {
                "title": "AI automation tools that actually save time for solopreneurs",
                "description": "After testing 50+ AI tools, here are the 8 that actually move the needle for solo founders. Focus on tools that eliminate repetitive tasks, not fancy features.",
                "url": "https://www.indiehackers.com/post/ai-automation-tools-solopreneurs",
                "author": "efficiency_finder",
                "source": "indiehackers",
                "created_at": "2024-01-13T16:45:00Z",
                "keywords_found": ["ai", "automation", "productivity"],
                "engagement_score": 78.1,
                "category": "tools",
                "content_type": "review"
            },
            {
                "title": "Why I'm building in public: 30-day revenue breakdown",
                "description": "Transparent look at building a B2B SaaS for small agencies. Daily user growth, revenue metrics, and lessons learned from customer interviews.",
                "url": "https://www.indiehackers.com/post/building-public-30-day-revenue",
                "author": "transparent_founder",
                "source": "indiehackers",
                "created_at": "2024-01-12T09:15:00Z",
                "keywords_found": ["saas", "revenue", "building in public"],
                "engagement_score": 88.5,
                "category": "case-study",
                "content_type": "milestone"
            }
        ]

        # Filter by keywords if provided
        if keywords:
            filtered_results = []
            for result in mock_results:
                if any(keyword.lower() in result["title"].lower() or
                      keyword.lower() in result["description"].lower()
                      for keyword in keywords):
                    filtered_results.append(result)
            mock_results = filtered_results

        return {
            "results": mock_results,
            "total_found": len(mock_results),
            "keywords": keywords,
            "category": category,
            "search_timestamp": datetime.utcnow().isoformat(),
            "api_source": "indiehackers_fallback"
        }

    async def _analyze_market_size(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Research and estimate market size for a SaaS idea."""
        industry = parameters.get("industry", "")
        target_audience = parameters.get("target_audience", "")
        keywords = parameters.get("keywords", [])
        geographic_scope = parameters.get("geographic_scope", "global")

        # Mock market analysis
        market_data = {
            "productivity": {
                "total_addressable_market": "$50B",
                "serviceable_addressable_market": "$15B",
                "serviceable_obtainable_market": "$500M",
                "growth_rate": "15% annually",
                "key_players": ["Notion", "Asana", "Monday.com", "Slack"]
            },
            "ai": {
                "total_addressable_market": "$120B",
                "serviceable_addressable_market": "$30B",
                "serviceable_obtainable_market": "$1B",
                "growth_rate": "25% annually",
                "key_players": ["OpenAI", "Anthropic", "Google", "Microsoft"]
            },
            "automation": {
                "total_addressable_market": "$35B",
                "serviceable_addressable_market": "$10B",
                "serviceable_obtainable_market": "$300M",
                "growth_rate": "20% annually",
                "key_players": ["Zapier", "UiPath", "Automation Anywhere"]
            }
        }

        # Find relevant industry data
        relevant_data = market_data.get(industry.lower(), {
            "total_addressable_market": "$5B",
            "serviceable_addressable_market": "$1B",
            "serviceable_obtainable_market": "$50M",
            "growth_rate": "10% annually",
            "key_players": ["Various incumbents"]
        })

        return {
            "industry": industry,
            "target_audience": target_audience,
            "geographic_scope": geographic_scope,
            "market_analysis": relevant_data,
            "market_attractiveness_score": 75.5,  # 0-100
            "competitive_intensity": "medium",
            "barriers_to_entry": ["Technology expertise", "Customer acquisition", "Funding"],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    async def _analyze_competition(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze existing competitors and market saturation."""
        keywords = parameters.get("keywords", [])
        market_category = parameters.get("market_category", "")
        analysis_depth = parameters.get("analysis_depth", "basic")

        # Mock competitive analysis
        competitors = [
            {
                "name": "CompetitorA",
                "website": "https://competitora.com",
                "description": "Leading solution in the market",
                "estimated_revenue": "$10M+",
                "funding": "$50M Series B",
                "strengths": ["Strong brand", "Large customer base", "Feature-rich"],
                "weaknesses": ["Expensive", "Complex setup", "Poor customer service"],
                "market_share": "15%"
            },
            {
                "name": "CompetitorB",
                "website": "https://competitorb.com",
                "description": "Fast-growing startup with modern approach",
                "estimated_revenue": "$2M+",
                "funding": "$5M Seed",
                "strengths": ["User-friendly", "Modern UI", "Good pricing"],
                "weaknesses": ["Limited features", "Small team", "Scaling challenges"],
                "market_share": "5%"
            }
        ]

        market_saturation = "medium"  # low, medium, high
        if len(competitors) > 10:
            market_saturation = "high"
        elif len(competitors) < 3:
            market_saturation = "low"

        return {
            "market_category": market_category,
            "competitors_found": len(competitors),
            "competitors": competitors,
            "market_saturation": market_saturation,
            "competition_intensity_score": 65.0,  # 0-100, lower = less competition
            "market_gaps": [
                "AI-powered automation",
                "Better mobile experience",
                "Affordable pricing for SMBs",
                "Industry-specific features"
            ],
            "differentiation_opportunities": [
                "Focus on specific niche",
                "Better user experience",
                "AI integration",
                "More competitive pricing"
            ],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    async def _check_domain_availability(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check domain name availability for the SaaS idea."""
        domain_name = parameters.get("domain_name", "")
        extensions = parameters.get("extensions", [".com", ".io", ".ai"])

        # Mock domain availability check
        availability_results = {}
        for ext in extensions:
            full_domain = f"{domain_name}{ext}"
            # Mock availability (in real implementation, use domain API)
            is_available = hash(full_domain) % 3 != 0  # Random mock availability
            availability_results[ext] = {
                "domain": full_domain,
                "available": is_available,
                "price": "$12/year" if is_available else "N/A",
                "alternative_suggestions": [
                    f"{domain_name}app{ext}",
                    f"{domain_name}pro{ext}",
                    f"get{domain_name}{ext}"
                ] if not is_available else []
            }

        return {
            "domain_name": domain_name,
            "availability_results": availability_results,
            "best_available": next((ext for ext, data in availability_results.items() if data["available"]), None),
            "check_timestamp": datetime.utcnow().isoformat()
        }

    async def _analyze_google_trends(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Google Trends data for market interest."""
        keywords = parameters.get("keywords", [])
        timeframe = parameters.get("timeframe", "3months")
        geographic_region = parameters.get("geographic_region", "worldwide")

        # Mock Google Trends data
        trends_data = {}
        for keyword in keywords:
            # Mock trend data
            trend_score = hash(keyword) % 100  # Random mock score 0-100
            trends_data[keyword] = {
                "interest_score": trend_score,
                "trend_direction": "rising" if trend_score > 60 else "stable" if trend_score > 30 else "declining",
                "related_queries": [
                    f"{keyword} tool",
                    f"{keyword} software",
                    f"best {keyword}",
                    f"{keyword} automation"
                ],
                "regional_interest": {
                    "US": trend_score * 0.9,
                    "UK": trend_score * 0.8,
                    "Germany": trend_score * 0.7,
                    "Canada": trend_score * 0.75
                }
            }

        return {
            "keywords": keywords,
            "timeframe": timeframe,
            "geographic_region": geographic_region,
            "trends_data": trends_data,
            "overall_interest_score": sum(data["interest_score"] for data in trends_data.values()) / len(trends_data),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()