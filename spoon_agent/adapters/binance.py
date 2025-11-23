"""Binance API adapter for fetching cryptocurrency market data."""

import logging
from datetime import datetime
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

# Stablecoins to exclude from analysis
STABLECOINS = {
    'USDCUSDT', 'FDUSDUSDT', 'TUSDUSDT', 'BUSDUSDT', 'DAIUSDT',
    'USDPUSDT', 'FRAXUSDT', 'LUSDUSDT', 'SUSDUSDT', 'USTCUSDT',
    'USDDUSDT', 'GUSDUSDT', 'PAXGUSDT', 'USTUSDT'
}


class BinanceAPIError(Exception):
    """Raised when Binance API request fails."""
    pass


class BinanceAdapter:
    """Adapter for Binance REST API."""

    BASE_URL = "https://api.binance.com/api/v3"

    async def fetch_24h_ticker(self) -> list[dict]:
        """
        Fetch 24-hour ticker data for all USDT pairs from Binance.

        Returns:
            List of USDT pairs with market data (price, volume, change %)

        Raises:
            BinanceAPIError: If API request fails
        """
        url = f"{self.BASE_URL}/ticker/24hr"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    error_msg = f"Binance API failed with status {response.status}"
                    logger.error(error_msg)
                    raise BinanceAPIError(error_msg)

                data = await response.json()

        # Filter and process USDT pairs
        usdt_pairs = []
        for item in data:
            if not isinstance(item, dict):
                continue

            symbol = item.get('symbol', '')
            if not symbol.endswith('USDT'):
                continue

            if symbol in STABLECOINS:
                continue

            # Validate required fields
            required_fields = ['symbol', 'priceChangePercent', 'volume', 'lastPrice']
            if not all(key in item for key in required_fields):
                continue

            usdt_pairs.append({
                'symbol': symbol,
                'priceChangePercent': float(item['priceChangePercent']),
                'volume': float(item['volume']),
                'lastPrice': float(item['lastPrice']),
                'count': int(item.get('count', 0)),
                'quoteVolume': float(item.get('quoteVolume', 0))
            })

        logger.info(f"Fetched {len(usdt_pairs)} USDT pairs from Binance")
        return usdt_pairs

    async def fetch_token_data(self, token: str) -> Optional[dict]:
        """
        Fetch 24-hour ticker data for a specific token.

        Args:
            token: Token symbol (e.g., "BTC", "ETH")

        Returns:
            Token data dict or None if not found

        Raises:
            BinanceAPIError: If API request fails
        """
        all_pairs = await self.fetch_24h_ticker()
        target_symbol = f"{token.upper()}USDT"

        token_data = next(
            (pair for pair in all_pairs if pair['symbol'] == target_symbol),
            None
        )

        if token_data:
            logger.info(f"Found {token} on Binance: ${token_data['lastPrice']}")
        else:
            logger.warning(f"Token {token} not found on Binance")

        return token_data

    async def fetch_multiple_tokens(self, tokens: list[str]) -> dict[str, dict]:
        """
        Fetch 24-hour ticker data for multiple tokens.

        Args:
            tokens: List of token symbols (e.g., ["BTC", "ETH", "SOL"])

        Returns:
            Dict mapping token symbols to their market data

        Raises:
            BinanceAPIError: If API request fails
        """
        all_pairs = await self.fetch_24h_ticker()
        target_symbols = {f"{token.upper()}USDT" for token in tokens}

        result = {}
        for pair in all_pairs:
            if pair['symbol'] in target_symbols:
                # Extract token symbol (remove USDT suffix)
                token = pair['symbol'][:-4]
                result[token] = pair

        logger.info(f"Found {len(result)}/{len(tokens)} tokens on Binance")
        return result
