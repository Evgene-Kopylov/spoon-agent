"""NATS worker for trading lead analysis with cryptocurrency market data."""

import asyncio
import logging
from typing import Any, Literal, Optional

from faststream import FastStream
from faststream.nats import NatsBroker
from pydantic import BaseModel

from spoon_agent.config import get_settings
from spoon_agent.graphs.trading_analysis import TradingAnalysisGraph
from spoon_agent.utils.formatters import format_trading_lead_reply

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("spoon_agent")

broker = NatsBroker(settings.nats_url)
app = FastStream(broker)

# Instantiate analysis graph once per worker
analysis_graph: Optional[TradingAnalysisGraph] = None


class TradingLeadPayload(BaseModel):
    """Payload for trading lead analysis from insight_worker."""

    chat_id: str
    sender_id: str
    reasoning: str
    messages: list[str]
    task_type: Literal["trading_lead_analysis"]


async def _publish_result(
    payload: TradingLeadPayload,
    *,
    status: str,
    reply: Optional[str] = None,
    analysis: Optional[dict[str, Any]] = None,
    error: Optional[dict[str, Any]] = None,
) -> None:
    """
    Publish analysis result to NATS.

    Args:
        payload: Original request payload
        status: Result status ("analysis_ready" or "analysis_error")
        reply: Formatted reply text for Telegram
        analysis: Full analysis result
        error: Error details if failed
    """
    result: dict[str, Any] = {
        "status": status,
        "chat_id": payload.chat_id,
        "sender_id": payload.sender_id,
        "task_type": payload.task_type,
    }

    if analysis is not None:
        result["analysis"] = analysis

    if reply:
        result["reply"] = reply

    if error is not None:
        result["error"] = error

    await broker.publish(result, subject=settings.insight_result_subject)
    logger.info(
        f"Published {status} for sender {payload.sender_id} to {settings.insight_result_subject}"
    )


@broker.subscriber(settings.spoon_analysis_subject)
async def handle_analysis_request(payload: TradingLeadPayload) -> None:
    """
    Handle trading lead analysis request from insight_worker.

    Args:
        payload: Trading lead payload with sender messages
    """
    global analysis_graph

    # Initialize graph on first request
    if analysis_graph is None:
        logger.info("Initializing trading analysis graph...")
        analysis_graph = TradingAnalysisGraph(settings)
        await analysis_graph.initialize()
        logger.info("Trading analysis graph ready")

    logger.info(
        f"Received analysis request for sender {payload.sender_id} "
        f"with {len(payload.messages)} messages"
    )

    # Run analysis
    try:
        analysis_result = await analysis_graph.run(
            chat_id=payload.chat_id,
            sender_id=payload.sender_id,
            reasoning=payload.reasoning,
            messages=payload.messages,
            task_type=payload.task_type
        )

        # Extract final summary
        final_summary = analysis_result.get("final_summary", "Анализ завершен.")

        # Format reply for Telegram
        reply_text = format_trading_lead_reply(
            sender_id=payload.sender_id,
            reasoning=payload.reasoning,
            final_summary=final_summary
        )

        # Prepare analysis result with all required fields
        analysis_with_all_fields = analysis_result.copy()
        
        # Add extracted_coins if missing
        if "extracted_coins" not in analysis_with_all_fields:
            analysis_with_all_fields["extracted_coins"] = analysis_result.get("selected_tokens", [])
        
        # Add token_reports if missing
        if "token_reports" not in analysis_with_all_fields:
            analysis_with_all_fields["token_reports"] = analysis_result.get("token_reports", {})
        
        # Add final_summary if missing
        if "final_summary" not in analysis_with_all_fields:
            analysis_with_all_fields["final_summary"] = final_summary

        # Publish successful result
        await _publish_result(
            payload,
            status="analysis_ready",
            reply=reply_text,
            analysis=analysis_with_all_fields,
        )

        logger.info(f"Analysis completed successfully for sender {payload.sender_id}")

    except Exception as exc:
        logger.error(
            f"Analysis failed for sender {payload.sender_id}: {exc}",
            exc_info=True
        )

        # Publish error result
        await _publish_result(
            payload,
            status="analysis_error",
            error={"message": str(exc)},
        )


async def main() -> None:
    """Run FastStream application."""
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
