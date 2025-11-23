import pytest

from spoon_agent.adapters.binance import BinanceAdapter
from spoon_agent.adapters.tavily import TavilyAdapter
from spoon_agent.graphs.trading_analysis import TradingAnalysisGraph
from spoon_toolkits.crypto.crypto_powerdata.tools import CryptoPowerDataCEXTool


@pytest.mark.asyncio
async def test_trading_analysis_graph_with_stubbed_dependencies(monkeypatch, settings):
    """Graph returns complete analysis when external calls are stubbed."""

    async def fake_fetch_multiple_tokens(self, tokens):
        return {
            token: {
                "symbol": f"{token}USDT",
                "priceChangePercent": 3.5,
                "volume": 12345.6,
                "lastPrice": 101.0 + idx,
                "quoteVolume": 20000.0,
            }
            for idx, token in enumerate(tokens)
        }

    async def fake_fetch_news(self, token, max_results=3, search_depth="basic"):
        return [{"title": f"{token} headline", "url": "http://example.com", "content": f"{token} news"}]

    async def fake_execute(self, **_kwargs):
        return type("Result", (), {"output": {"ema": [1, 2, 3]}, "error": None})()

    monkeypatch.setattr(BinanceAdapter, "fetch_multiple_tokens", fake_fetch_multiple_tokens)
    monkeypatch.setattr(TavilyAdapter, "fetch_news", fake_fetch_news)
    monkeypatch.setattr(CryptoPowerDataCEXTool, "execute", fake_execute)

    graph = TradingAnalysisGraph(settings)

    class DummyResp:
        def __init__(self, content: str):
            self.content = content

    async def stub_chat(messages):
        prompt = messages[-1].content if messages else ""
        if "Extract all cryptocurrency ticker symbols" in prompt:
            return DummyResp("BTC, SOL")
        if "TECHNICAL trading recommendation" in prompt:
            token = prompt.split("for ")[1].split("\n")[0].strip()
            return DummyResp(f"TA for {token}")
        if "NEWS for" in prompt:
            token = prompt.split("NEWS for")[1].split(",")[0].strip()
            return DummyResp(f"News for {token}")
        if "Ты крипто-аналитик" in prompt:
            return DummyResp("Итоговый отчет по BTC и SOL")
        return DummyResp("stub")

    monkeypatch.setattr(graph.llm, "chat", stub_chat)

    result = await graph.run(
        chat_id="chat-123",
        sender_id="user-456",
        reasoning="интерес к рынку",
        messages=["Думаю про BTC", "SOL тоже интересен"],
    )

    assert result["extracted_coins"] == ["BTC", "SOL"]
    assert result["selected_tokens"] == ["BTC", "SOL"]
    assert result["binance_market_data"]["source"] == "binance_api"
    assert set(result["token_reports"].keys()) == {"BTC", "SOL"}
    assert result["token_scores"]["BTC"] >= 0
    assert result["final_summary"]
