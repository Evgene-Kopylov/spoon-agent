import pytest

import spoon_agent.main as main
from spoon_agent.main import TradingLeadPayload


class _FakeGraph:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.initialized = False
        self.run_called_with = None

    async def initialize(self):
        self.initialized = True

    async def run(self, **kwargs):
        self.run_called_with = kwargs
        if self.should_fail:
            raise RuntimeError("graph boom")
        return {
            "final_summary": "готовый отчет",
            "extracted_coins": ["BTC"],
            "token_reports": {"BTC": {"technical_analysis": "ok", "news_analysis": "ok"}},
        }


@pytest.mark.asyncio
async def test_handle_analysis_request_publishes_ready(reset_main, monkeypatch):
    fake_graph = _FakeGraph()
    monkeypatch.setattr(main, "TradingAnalysisGraph", lambda _settings: fake_graph)

    payload = TradingLeadPayload(
        chat_id="chat-1",
        sender_id="sender-1",
        reasoning="interested in BTC",
        messages=["BTC to the moon"],
        task_type="trading_lead_analysis",
    )

    await main.handle_analysis_request(payload)

    assert fake_graph.initialized is True
    assert fake_graph.run_called_with["sender_id"] == "sender-1"

    assert len(reset_main.broker.published) == 1
    message = reset_main.broker.published[0]["message"]

    assert message["status"] == "analysis_ready"
    assert message["chat_id"] == "chat-1"
    assert message["analysis"]["final_summary"] == "готовый отчет"
    assert "Анализ потенциального клиента" in message["reply"]


@pytest.mark.asyncio
async def test_handle_analysis_request_publishes_error(reset_main, monkeypatch):
    fake_graph = _FakeGraph(should_fail=True)
    monkeypatch.setattr(main, "TradingAnalysisGraph", lambda _settings: fake_graph)

    payload = TradingLeadPayload(
        chat_id="chat-2",
        sender_id="sender-2",
        reasoning="interested in SOL",
        messages=["SOL update"],
        task_type="trading_lead_analysis",
    )

    await main.handle_analysis_request(payload)

    assert len(reset_main.broker.published) == 1
    message = reset_main.broker.published[0]["message"]

    assert message["status"] == "analysis_error"
    assert message["error"]["message"] == "graph boom"
