"""Utility functions for formatting analysis results."""


def format_trading_lead_reply(
    sender_id: str,
    reasoning: str,
    final_summary: str
) -> str:
    """
    Format trading lead analysis result for Telegram.

    Args:
        sender_id: Telegram user ID (sender)
        reasoning: Reasoning why this is a potential client
        final_summary: Final analysis summary from LLM (Russian)

    Returns:
        Formatted message for Telegram
    """
    # Ensure final_summary is not None
    summary_text = final_summary if final_summary else "Анализ недоступен"

    lines = [
        "Анализ потенциального клиента",
        "",
        f"Отправитель: {sender_id}",
        f"Причина: {reasoning[:200]}...",  # Truncate if too long
        "",
        "Анализ рынка:",
        summary_text
    ]

    return "\n".join(lines)


def format_coin_list(coins: list[str]) -> str:
    """
    Format list of coins for display.

    Args:
        coins: List of cryptocurrency ticker symbols

    Returns:
        Formatted coin list string
    """
    if not coins:
        return "Нет монет"

    return ", ".join(coins)
