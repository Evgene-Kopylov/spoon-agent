"""Prompt for extracting cryptocurrency mentions from user messages."""


def get_coin_extraction_prompt(messages: list[str]) -> str:
    """
    Generate prompt for extracting cryptocurrency tickers from trading messages.

    Args:
        messages: List of user messages from trading chat

    Returns:
        Prompt string for LLM to extract coin symbols
    """
    messages_text = "\n".join(f"- {msg}" for msg in messages)

    return f"""You are a cryptocurrency trading analyst. Extract all cryptocurrency ticker symbols mentioned in the following messages.

Messages from trading chat:
{messages_text}

Requirements:
1. Identify all cryptocurrency tickers (e.g., BTC, ETH, SOL, BNB, XRP)
2. Return only valid ticker symbols (uppercase, 2-10 characters)
3. Exclude stablecoins (USDT, USDC, BUSD, DAI, etc.)
4. If multiple variations of the same coin (e.g., "bitcoin", "BTC"), return the ticker
5. Return as comma-separated list

Output format: BTC,ETH,SOL (or empty string if no coins mentioned)

Extract tickers:"""
