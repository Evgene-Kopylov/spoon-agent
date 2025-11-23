"""Tavily API adapter for fetching cryptocurrency news."""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class TavilyAdapter:
    """Adapter for Tavily API (news search)."""

    def __init__(self, api=None, api_key: Optional[str] = None):
        """
        Initialize Tavily adapter.

        Args:
            api: SpoonAI HighLevelGraphAPI instance with MCP tool access (optional)
            api_key: Tavily API key for direct API access (optional)
        """
        self.api = api
        self.api_key = api_key
        self.tool = None
        self.tavily_url = "https://api.tavily.com/search"

    async def initialize(self) -> bool:
        """
        Initialize Tavily (MCP tool or direct API).

        Returns:
            True if tool is available, False otherwise
        """
        # Try direct API key first
        if self.api_key:
            logger.info("Tavily direct API initialized with API key")
            return True

        # Fallback to MCP tool
        if self.api is None:
            logger.info("Tavily not configured (news analysis disabled)")
            return False

        try:
            self.tool = self.api.create_mcp_tool("tavily-search")
            if self.tool:
                logger.info("Tavily MCP tool initialized successfully")
                return True
            else:
                logger.warning("Tavily MCP tool not available")
                return False
        except Exception as exc:
            logger.error(f"Failed to initialize Tavily tool: {exc}")
            return False

    async def fetch_news(
        self,
        token: str,
        max_results: int = 3,
        search_depth: str = "basic"
    ) -> list[dict]:
        """
        Fetch cryptocurrency news for a specific token.

        Args:
            token: Token symbol (e.g., "BTC", "ETH")
            max_results: Maximum number of news results to return
            search_depth: Search depth ("basic" or "advanced")

        Returns:
            List of news items with title, url, content
        """
        # Use direct API if available
        if self.api_key:
            return await self._fetch_news_direct_api(token, max_results, search_depth)

        # Fallback to MCP tool
        if not self.tool:
            logger.debug(f"Tavily tool not initialized, skipping news for {token}")
            return []

        return await self._fetch_news_mcp(token, max_results, search_depth)

    async def _fetch_news_direct_api(
        self,
        token: str,
        max_results: int,
        search_depth: str
    ) -> list[dict]:
        """Fetch news using direct Tavily API."""
        query = f"{token} cryptocurrency news price analysis market trends"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.tavily_url,
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "max_results": max_results,
                        "search_depth": search_depth,
                        "include_answer": False,
                        "include_raw_content": False,
                    }
                )
                response.raise_for_status()
                data = response.json()

            # Parse Tavily API response
            results = data.get("results", [])
            items = [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": (item.get("content", "") or "")[:400],
                }
                for item in results
            ]

            logger.info(f"Fetched {len(items)} news items for {token} via direct API")
            return items

        except Exception as exc:
            logger.error(f"Tavily direct API search failed for {token}: {exc}")
            return []

    async def _fetch_news_mcp(
        self,
        token: str,
        max_results: int,
        search_depth: str
    ) -> list[dict]:
        """Fetch news using MCP tool."""
        query = f"{token} cryptocurrency news price analysis market trends"

        try:
            result = await self.tool.execute(
                query=query,
                max_results=max_results,
                search_depth=search_depth
            )
            payload = result.output if hasattr(result, "output") else result
        except Exception as exc:
            logger.error(f"Tavily MCP search failed for {token}: {exc}")
            return []

        # Parse response
        items = []
        if isinstance(payload, list):
            items = [
                {
                    "title": entry.get("title", ""),
                    "url": entry.get("url", ""),
                    "content": (entry.get("content", "") or "")[:400],
                }
                for entry in payload
                if isinstance(entry, dict)
            ]
        elif isinstance(payload, str):
            items = [{
                "title": "Summary",
                "url": "",
                "content": payload[:400]
            }]

        logger.info(f"Fetched {len(items)} news items for {token} via MCP")
        return items

    async def fetch_multiple_tokens(
        self,
        tokens: list[str],
        max_results_per_token: int = 3
    ) -> dict[str, list[dict]]:
        """
        Fetch news for multiple tokens.

        Args:
            tokens: List of token symbols
            max_results_per_token: Max results per token

        Returns:
            Dict mapping token symbols to their news items
        """
        result = {}
        for token in tokens:
            news_items = await self.fetch_news(token, max_results=max_results_per_token)
            result[token] = news_items

        return result
