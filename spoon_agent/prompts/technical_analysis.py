"""Prompt for technical analysis of cryptocurrency tokens."""


def get_technical_analysis_prompt(
    token: str,
    current_price: float,
    price_change_24h: float,
    ta_section: str
) -> str:
    """
    Generate prompt for LLM-powered technical analysis.

    Args:
        token: Cryptocurrency ticker symbol (e.g., "BTC")
        current_price: Current price in USD
        price_change_24h: 24-hour price change percentage
        ta_section: Formatted technical analysis data (indicators, levels)

    Returns:
        Prompt string for LLM technical analysis
    """
    return f"""You are a professional crypto trading analyst. Provide a concise, actionable TECHNICAL trading recommendation for {token}.

Context:
- Token: {token}
- Current Price: ${current_price}
- 24h Change: {price_change_24h:+.2f}%

Technical Data (1d and 4h):
{ta_section}

Requirements:
1) Summarize technical trend and momentum
2) Key support/resistance levels (prices)
3) Entry plan (zones or triggers)
4) Stop loss
5) Targets (multiple if applicable)
6) Risk rating (Low/Medium/High) and a 1-10 opportunity score
Output in English, concise, bullet style."""
