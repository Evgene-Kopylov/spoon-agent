"""Graph nodes for extracting cryptocurrency mentions from messages."""

import logging
from typing import Any

from spoon_ai.schema import Message

from spoon_agent.prompts.coin_extraction import get_coin_extraction_prompt

logger = logging.getLogger(__name__)


async def extract_coins_from_messages(
    state: dict[str, Any],
    llm,
    default_coins: list[str]
) -> dict[str, Any]:
    """
    Extract cryptocurrency ticker symbols from trading messages.

    Uses LLM to identify coin mentions in messages. If no coins found,
    falls back to default popular coins list.

    Args:
        state: Graph state containing 'messages' field
        llm: LLM instance for extraction
        default_coins: Fallback list of popular coins (e.g., ["BTC", "ETH"])

    Returns:
        Updated state with 'extracted_coins' and 'coin_extraction_method' fields
    """
    messages = state.get("messages", [])
    if not messages:
        logger.warning("No messages provided, using default coins")
        return {
            "extracted_coins": default_coins,
            "coin_extraction_method": "fallback_default",
            "extraction_log": ["No messages, using default coins"]
        }

    # Build prompt for LLM
    prompt = get_coin_extraction_prompt(messages)

    # Extract coins using LLM
    try:
        response = await llm.chat([Message(role="user", content=prompt)])
        extracted_text = response.content.strip()

        # Parse comma-separated list
        if extracted_text and extracted_text.lower() not in ["none", "no coins", ""]:
            coins = [
                coin.strip().upper()
                for coin in extracted_text.split(",")
                if coin.strip()
            ]
            # Filter valid tickers (2-10 chars, uppercase letters)
            coins = [
                coin for coin in coins
                if 2 <= len(coin) <= 10 and coin.isalpha()
            ]

            if coins:
                logger.info(f"Extracted {len(coins)} coins from messages: {coins}")
                return {
                    "extracted_coins": coins,
                    "coin_extraction_method": "llm_extraction",
                    "extraction_log": [f"LLM extracted: {', '.join(coins)}"]
                }

    except Exception as exc:
        logger.error(f"LLM extraction failed: {exc}")

    # Fallback to default coins
    logger.info(f"No coins extracted, using default: {default_coins}")
    return {
        "extracted_coins": default_coins,
        "coin_extraction_method": "fallback_default",
        "extraction_log": ["LLM extraction failed or no coins found, using default"]
    }
