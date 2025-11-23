# Spoon Agent tests

Test suite for spoon_agent: fast unit tests plus one live end-to-end run through real services.

## Layout
```
tests/
├── README.md                        # This guide
├── conftest.py                      # Fixtures, dependency stubs
├── test_main_handler.py             # Unit: publishes success/error results
├── test_trading_analysis_graph.py   # Unit: graph with stubbed external APIs
└── test_spoon_agent_live.py         # Integration: real request → real response
```

## Scenarios
- Unit tests (fast, no external services): mock Binance/Tavily/PowerData, use an in-memory broker.
+- Integration test (slow, needs network): publishes a task to `spoon.analysis` and waits for a real result on `insight.results` from a running spoon_agent.

## Requirements for the integration test
- spoon_agent and NATS are running (e.g., `docker compose up spoon-agent nats`).
- `.env` contains real keys: `OPENAI_API_KEY` (or Ollama-compatible), `TAVILY_API_KEY` if you want news, and other variables from `spoon_agent/config.py`.
- Internet access for Binance/Tavily/LLM.

## How to run
```bash
# unit tests only (skip integration)
uv run pytest -q -m "not integration"

# full run with the live scenario (can take ~5 minutes)
uv run pytest -s -v
```

## What is covered
- `test_main_handler.py`: `handle_analysis_request` publishes correct payloads for success and error paths.
- `test_trading_analysis_graph.py`: the graph walks all nodes, builds a report, and returns tokens/summary (external calls stubbed).
- `test_spoon_agent_live.py`: real NATS roundtrip; verifies `analysis_ready`/`analysis_error`, `final_summary`, and coin lists.
