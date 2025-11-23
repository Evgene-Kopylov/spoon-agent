"""Prompt for news-driven sentiment analysis of cryptocurrency tokens."""


def get_news_analysis_prompt(
    token: str,
    current_price: float,
    news_section: str
) -> str:
    """
    Generate prompt for LLM-powered news sentiment analysis.

    Args:
        token: Cryptocurrency ticker symbol (e.g., "BTC")
        current_price: Current price in USD
        news_section: Formatted news data (headlines, snippets, sources)

    Returns:
        Prompt string for LLM news analysis
    """
    return f"""You are a professional crypto news/sentiment analyst. Based on recent NEWS for {token}, provide a concise, actionable NEWS-DRIVEN trading recommendation.

Context:
- Token: {token}
- Current Price: ${current_price}

News Data (headlines, snippets, sources):
{news_section}

Requirements:
1) Summarize news sentiment and key events
2) Impact on price (bullish/bearish/neutral)
3) Trading implications (buy/sell/hold)
4) Risk factors from news
5) Confidence level (1-10)
Output in English, concise, bullet style."""
