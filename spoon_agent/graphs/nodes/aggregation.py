"""Graph nodes for aggregating token analysis into final report."""

import logging
from typing import Any, Optional

from spoon_ai.schema import Message

from spoon_agent.prompts.final_report import get_final_report_prompt

logger = logging.getLogger(__name__)


async def aggregate_results(
    state: dict[str, Any],
    llm,
    config: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Aggregate all token analyses into final Russian-language report.

    Args:
        state: Graph state containing token_reports and selected_tokens
        llm: LLM instance for aggregation
        config: Optional configuration

    Returns:
        Updated state with 'final_summary' field
    """
    token_reports = state.get("token_reports", {})
    selected_tokens = state.get("selected_tokens", [])

    if not token_reports:
        logger.warning("No token reports to aggregate")
        return {
            "final_summary": "Нет данных для анализа.",
            "execution_log": (state.get("execution_log") or []) + ["No reports to aggregate"]
        }

    # Filter out error reports
    valid_reports = {
        token: report
        for token, report in token_reports.items()
        if "error" not in report
    }

    if not valid_reports:
        logger.warning("All token analyses failed")
        return {
            "final_summary": "Анализ всех токенов завершился с ошибкой.",
            "execution_log": (state.get("execution_log") or []) + ["All analyses failed"]
        }

    # Build prompt for final aggregation
    allowed_tokens = list(valid_reports.keys())
    target_token = allowed_tokens[0] if allowed_tokens else None

    # Extract only essential fields to reduce token usage
    essential_reports = {}
    for token, report in valid_reports.items():
        # Handle technical analysis (could be string or dict)
        tech_analysis = report.get("technical_analysis", {})
        if isinstance(tech_analysis, str):
            # If it's a string, create minimal structure
            essential_tech = {
                "summary": tech_analysis[:200] if tech_analysis else "No technical analysis"
            }
        else:
            # If it's a dict, extract key fields
            essential_tech = {
                "sentiment": tech_analysis.get("sentiment"),
                "trend": tech_analysis.get("trend"),
                "risk_level": tech_analysis.get("risk_level"),
                "support_level": tech_analysis.get("support_level"),
                "resistance_level": tech_analysis.get("resistance_level")
            }
        
        # Handle news analysis (could be string or dict)
        news_analysis = report.get("news_analysis", {})
        if isinstance(news_analysis, str):
            # If it's a string, create minimal structure
            essential_news = {
                "summary": news_analysis[:200] if news_analysis else "No news analysis"
            }
        else:
            # If it's a dict, extract key fields
            essential_news = {
                "sentiment": news_analysis.get("sentiment"),
                "key_events": news_analysis.get("key_events"),
                "summary": news_analysis.get("summary")
            }
        
        essential_reports[token] = {
            "current_price": report.get("current_price"),
            "price_change_24h": report.get("price_change_24h"),
            "volume_24h": report.get("volume_24h"),
            "market_cap": report.get("market_cap"),
            "technical_analysis": essential_tech,
            "news_analysis": essential_news
        }

    prompt = get_final_report_prompt(
        token_reports=essential_reports,
        allowed_tokens=allowed_tokens,
        target_token=target_token,
        reasoning=state.get("reasoning"),
        messages=state.get("messages")
    )

    # Generate final summary using LLM
    try:
        response = await llm.chat([Message(role="user", content=prompt)])
        final_summary = response.content.strip()

        logger.info(f"Final report generated for {len(allowed_tokens)} tokens")

        log = list(state.get("execution_log") or [])
        log.append(f"Final aggregation completed for {len(allowed_tokens)} tokens")

        return {
            "final_summary": final_summary,
            "execution_log": log
        }

    except Exception as exc:
        logger.error(f"Final aggregation failed: {exc}")

        # Fallback: create simple summary
        fallback_summary = _create_fallback_summary(valid_reports, allowed_tokens)

        return {
            "final_summary": fallback_summary,
            "error": str(exc),
            "execution_log": (state.get("execution_log") or []) + [f"Aggregation failed: {exc}"]
        }


def _create_fallback_summary(reports: dict[str, Any], tokens: list[str]) -> str:
    """Create simple fallback summary without LLM."""
    lines = [f"Анализ криптовалют: {', '.join(tokens)}", ""]

    for token in tokens:
        report = reports.get(token, {})
        price = report.get("current_price", 0)
        change = report.get("price_change_24h", 0)

        lines.append(f"{token}:")
        lines.append(f"  Цена: ${price:.2f} ({change:+.2f}%)")
        lines.append("")

    return "\n".join(lines)
