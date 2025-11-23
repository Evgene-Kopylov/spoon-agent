"""Live integration test for spoon_agent end-to-end processing.

Requires:
- Running spoon_agent service (e.g., via docker-compose)
- Accessible NATS broker (settings.nats_url)
- Valid API keys in environment (.env) for OpenAI/Ollama, Binance access, Tavily if used.

This test publishes a real task to spoon.analysis and waits for the agent
to produce a result on insight.results. No mocks are used.
"""

import asyncio
import json
import time

import os

import pytest
from nats.aio.client import Client as NATS

from spoon_agent.config import get_settings


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_spoon_agent_live_roundtrip():
    settings = get_settings()

    # Ensure we have credentials; skip early if not configured
    import os

    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not set; live test requires real credentials")

    nc = NATS()
    try:
        await nc.connect(servers=[settings.nats_url])
    except Exception as exc:
        pytest.skip(f"NATS unavailable at {settings.nats_url}: {exc}")

    results: list[dict] = []

    async def _on_result(msg):
        try:
            payload = json.loads(msg.data.decode())
        except Exception:
            payload = {"raw": msg.data.decode()}
        results.append(payload)

    # Subscribe to results before publishing
    await nc.subscribe(settings.insight_result_subject, cb=_on_result)

    sender_id = f"live_sender_{int(time.time())}"
    payload = {
        "chat_id": "live_chat_test",
        "sender_id": sender_id,
        "reasoning": "Пользователь спрашивает о стратегиях BTC/SOL",
        "messages": [
            "Хочу торговать BTC, что скажете про стратегию?",
            "SOL тоже интересна, есть ли новости?",
        ],
        "task_type": "trading_lead_analysis",
    }

    await nc.publish(settings.spoon_analysis_subject, json.dumps(payload).encode())
    await nc.flush()

    # Wait for matching result
    timeout = 320.0  # Allow time for Binance + news + LLM
    deadline = asyncio.get_event_loop().time() + timeout

    result = None
    while asyncio.get_event_loop().time() < deadline:
        result = next((r for r in results if r.get("sender_id") == sender_id), None)
        if result:
            break
        await asyncio.sleep(2)

    await nc.close()

    if not result:
        pytest.fail(f"Did not receive result for sender {sender_id} within {timeout}s")

    assert result["status"] in {"analysis_ready", "analysis_error"}
    assert result["chat_id"] == payload["chat_id"]

    if result["status"] == "analysis_ready":
        analysis = result.get("analysis") or {}
        assert analysis.get("final_summary"), "final_summary must be present"
        assert isinstance(analysis.get("extracted_coins", []), list)
        assert "token_reports" in analysis
