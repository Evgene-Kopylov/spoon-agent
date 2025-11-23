"""Graph nodes for fetching market data from Binance."""

import logging
from datetime import datetime
from typing import Any, Optional

from spoon_agent.adapters.binance import BinanceAdapter

logger = logging.getLogger(__name__)


async def fetch_binance_data(
    state: dict[str, Any],
    config: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Fetch market data from Binance for extracted coins.

    Args:
        state: Graph state containing 'extracted_coins' field
        config: Optional configuration

    Returns:
        Updated state with 'binance_market_data' field
    """
    coins = state.get("extracted_coins", [])
    if not coins:
        logger.error("No coins to fetch data for")
        return {
            "binance_market_data": None,
            "execution_log": (state.get("execution_log") or []) + ["No coins to fetch"]
        }

    adapter = BinanceAdapter()

    try:
        # Fetch data for all extracted coins
        market_data = await adapter.fetch_multiple_tokens(coins)

        # Filter out coins not found on Binance
        found_coins = list(market_data.keys())
        missing_coins = set(coins) - set(found_coins)

        if missing_coins:
            logger.warning(f"Coins not found on Binance: {missing_coins}")

        log = list(state.get("execution_log") or [])
        log.append(f"Fetched Binance data for {len(found_coins)} coins")

        return {
            "binance_market_data": {
                "token_data": market_data,
                "found_coins": found_coins,
                "missing_coins": list(missing_coins),
                "timestamp": datetime.now().isoformat(),
                "source": "binance_api"
            },
            "execution_log": log
        }

    except Exception as exc:
        logger.error(f"Failed to fetch Binance data: {exc}")
        return {
            "binance_market_data": None,
            "error": str(exc),
            "execution_log": (state.get("execution_log") or []) + [f"Binance fetch failed: {exc}"]
        }


async def prepare_token_list(
    state: dict[str, Any],
    config: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Prepare token list from Binance market data for analysis.

    Args:
        state: Graph state containing 'binance_market_data' field
        config: Optional configuration

    Returns:
        Updated state with 'selected_tokens' and 'token_details' fields
    """
    market_data = state.get("binance_market_data")
    if not market_data or not market_data.get("token_data"):
        logger.error("No market data available")
        return {
            "selected_tokens": [],
            "token_details": {},
            "execution_log": (state.get("execution_log") or []) + ["No market data to prepare"]
        }

    token_data = market_data["token_data"]
    selected_tokens = list(token_data.keys())

    # Extract token details for analysis
    token_details = {}
    for token, data in token_data.items():
        token_details[token] = {
            "symbol": data["symbol"],
            "price": data["lastPrice"],
            "price_change_24h": data["priceChangePercent"],
            "volume": data["volume"],
            "quote_volume": data["quoteVolume"]
        }

    log = list(state.get("execution_log") or [])
    log.append(f"Prepared {len(selected_tokens)} tokens for analysis")

    logger.info(f"Prepared tokens: {selected_tokens}")

    return {
        "selected_tokens": selected_tokens,
        "token_details": token_details,
        "execution_log": log
    }
