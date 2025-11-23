"""Prompt for final Russian-language report generation for Telegram."""

import json


def get_final_report_prompt(
    token_reports: dict,
    allowed_tokens: list[str],
    target_token: str | None = None,
    reasoning: str | None = None,
    messages: list[str] | None = None
) -> str:
    """
    Generate prompt for LLM to create final Russian-language trading report.

    Args:
        token_reports: Dict mapping token symbols to their analysis reports
        allowed_tokens: List of tokens that should be included in report
        target_token: Primary token to focus on (optional)
        reasoning: Why this user is a potential client (optional)
        messages: User messages (optional)

    Returns:
        Prompt string for LLM final aggregation (Russian output)
    """
    allowed_tokens_str = ", ".join(allowed_tokens)

    # Add context if available
    context_section = ""
    if reasoning or messages:
        context_section = "\nКонтекст потенциального клиента:"
        if reasoning:
            context_section += f"\n• Причина интереса: {reasoning}"
        if messages:
            msg_preview = " | ".join(messages[:3])[:200]  # First 3 messages, max 200 chars
            context_section += f"\n• Сообщения пользователя: {msg_preview}"
        context_section += "\n"

    return f"""Ты крипто-аналитик. Составь короткий отчет для сохранения в Telegram Saved Messages.
{context_section}
Данные по токенам (JSON, не добавляй других монет):
{json.dumps(token_reports, indent=2, ensure_ascii=False)}

Только эти токены: {allowed_tokens_str}. Никаких других активов и "гипотетических" примеров.

ВАЖНО: В данных по каждому токену есть поля "technical_analysis" и "news_analysis".
ОБЯЗАТЕЛЬНО используй эти поля для создания репорта! Не игнорируй их!

Формат (до 12 строк, без воды):
- заголовок: "{target_token or allowed_tokens[0]} — краткий разбор"
- затем по каждому токену из списка: один блок с 4–5 буллетами:
  • тренд/сентимент (из technical_analysis) и ключевые уровни (support/resistance)
  • план: вход/цель/стоп (если данных нет — скажи «план: данных мало»)
  • риск: Low/Medium/High (из technical_analysis или news_analysis)
  • новости/фактор: суммируй news_analysis (сентимент, ключевые события). Только если news_analysis пустой - пиши «новостей нет»
- финальная строка: общий вывод по токену(ам) в 1 предложении.

Требования: пиши по-русски, коротко, не придумывай цены/уровни вне переданных данных, не упоминай активы вне {allowed_tokens_str}."""
