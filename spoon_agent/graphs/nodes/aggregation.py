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

    prompt = get_final_report_prompt(
        token_reports=valid_reports,
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
