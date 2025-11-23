"""Graph nodes for cryptocurrency token analysis (TA + News)."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from spoon_ai.schema import Message

from spoon_agent.prompts.technical_analysis import get_technical_analysis_prompt
from spoon_agent.prompts.news_analysis import get_news_analysis_prompt

logger = logging.getLogger(__name__)


async def analyze_token(
    token: str,
    state: dict[str, Any],
    llm,
    powerdata_tool,
    tavily_adapter,
    config: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Perform complete analysis of a single cryptocurrency token.

    Combines technical analysis (TA) using indicators and news sentiment analysis.

    Args:
        token: Token symbol (e.g., "BTC", "ETH")
        state: Graph state containing token details
        llm: LLM instance for analysis
        powerdata_tool: CryptoPowerDataCEX tool for kline data
        tavily_adapter: Tavily adapter for news fetching
        config: Optional configuration

    Returns:
        Updated state with token analysis report
    """
    logger.info(f"Analyzing token: {token}")

    try:
        token_details = state.get("token_details", {})
        token_detail = token_details.get(token, {})

        # Fetch kline data and news in parallel
        kline_data = await _fetch_kline_data(token, powerdata_tool)
        news_data = await _fetch_news(token, tavily_adapter)

        # Extract token info
        current_price = token_detail.get("price", 0)
        price_change_24h = token_detail.get("price_change_24h", 0)

        # Format data for prompts
        ta_section = json.dumps(kline_data, indent=2, ensure_ascii=False) if kline_data.get("daily_data") else "TA unavailable"
        news_section = json.dumps(news_data, indent=2, ensure_ascii=False) if news_data else "News unavailable"

        # Build prompts
        ta_prompt = get_technical_analysis_prompt(token, current_price, price_change_24h, ta_section)
        news_prompt = get_news_analysis_prompt(token, current_price, news_section)

        # Run LLM analysis in parallel
        ta_response, news_response = await asyncio.gather(
            llm.chat([Message(role="user", content=ta_prompt)]),
            llm.chat([Message(role="user", content=news_prompt)])
        )

        # Build report
        report = {
            "token": token,
            "symbol": f"{token}/USDT",
            "technical_analysis": ta_response.content.strip(),
            "news_analysis": news_response.content.strip(),
            "current_price": current_price,
            "price_change_24h": price_change_24h,
            "indicators": kline_data,
            "news": news_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Update state
        token_reports = dict(state.get("token_reports") or {})
        token_reports[token] = report

        token_scores = dict(state.get("token_scores") or {})
        token_scores[token] = _score_token(report)

        log = list(state.get("execution_log") or [])
        log.append(f"Analysis completed for {token}")

        logger.info(f"Successfully analyzed {token}")

        return {
            "token_reports": token_reports,
            "token_scores": token_scores,
            "execution_log": log
        }

    except Exception as exc:
        logger.error(f"Analysis failed for {token}: {exc}")

        # Return error report
        token_reports = dict(state.get("token_reports") or {})
        token_reports[token] = {
            "error": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        log = list(state.get("execution_log") or [])
        log.append(f"Analysis failed for {token}: {exc}")

        return {
            "token_reports": token_reports,
            "execution_log": log
        }


async def _fetch_kline_data(token: str, powerdata_tool) -> dict[str, Any]:
    """Fetch kline data with technical indicators from PowerData tool."""
    try:
        if not powerdata_tool:
            return {"error": "PowerData tool not available", "data": None}

        symbol = f"{token}/USDT"
        indicators_config = {
            "rsi": [{"timeperiod": 14}],
            "ema": [{"timeperiod": 12}, {"timeperiod": 26}, {"timeperiod": 50}],
            "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
            "bbands": [{"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2}],
        }

        # Fetch daily and 4h data in parallel
        daily_result, h4_result = await asyncio.gather(
            powerdata_tool.execute(
                exchange="binance",
                symbol=symbol,
                timeframe="1d",
                limit=100,
                indicators_config=json.dumps(indicators_config),
                use_enhanced=True,
            ),
            powerdata_tool.execute(
                exchange="binance",
                symbol=symbol,
                timeframe="4h",
                limit=100,
                indicators_config=json.dumps(indicators_config),
                use_enhanced=True,
            )
        )

        return {
            "daily_data": daily_result.output if daily_result and not daily_result.error else None,
            "h4_data": h4_result.output if h4_result and not h4_result.error else None,
            "error": None,
        }

    except Exception as exc:
        logger.error(f"Kline fetch failed for {token}: {exc}")
        return {"error": str(exc), "data": None}


async def _fetch_news(token: str, tavily_adapter) -> dict[str, Any]:
    """Fetch news data for token using Tavily adapter."""
    try:
        news_items = await tavily_adapter.fetch_news(token, max_results=3)
        return {"data": news_items, "error": None}
    except Exception as exc:
        logger.error(f"News fetch failed for {token}: {exc}")
        return {"error": str(exc), "data": None}


def _score_token(report: dict[str, Any]) -> float:
    """
    Heuristic scoring for token based on analysis report.

    Returns:
        Score between 0.0 and 1.0
    """
    # Simple heuristic scoring
    score = 0.5  # Neutral base score

    # Adjust based on price change
    price_change = report.get("price_change_24h", 0)
    if price_change > 5:
        score += 0.2
    elif price_change < -5:
        score -= 0.2

    # Adjust based on analysis content (keyword matching)
    ta_text = report.get("technical_analysis", "").lower()
    news_text = report.get("news_analysis", "").lower()

    positive_keywords = ["bullish", "buy", "support", "uptrend", "positive"]
    negative_keywords = ["bearish", "sell", "resistance", "downtrend", "negative"]

    for keyword in positive_keywords:
        if keyword in ta_text or keyword in news_text:
            score += 0.05

    for keyword in negative_keywords:
        if keyword in ta_text or keyword in news_text:
            score -= 0.05

    # Clamp score to [0, 1]
    return max(0.0, min(1.0, score))
