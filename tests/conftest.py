"""Test configuration with lightweight stubs for external dependencies."""

import inspect
import logging
import os
import sys
import types
from pathlib import Path

import pytest

# Minimal env so pydantic Settings can load without real secrets when running unit tests
os.environ.setdefault("OPENAI_API_KEY", "test-key")

# Ensure project root is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _install_spoon_ai_stub() -> None:
    """Provide a tiny in-memory implementation of spoon_ai used in unit tests."""
    try:  # Prefer real package if installed
        import importlib

        importlib.import_module("spoon_ai")  # type: ignore
        return
    except Exception:
        pass

    if "spoon_ai" in sys.modules:
        return

    spoon_ai = types.ModuleType("spoon_ai")

    schema = types.ModuleType("spoon_ai.schema")

    class Message:
        def __init__(self, role: str, content: str):
            self.role = role
            self.content = content

    schema.Message = Message

    graph_mod = types.ModuleType("spoon_ai.graph")
    END = "END"

    class _CompiledGraph:
        def __init__(self, entry_point, nodes, edges):
            self.entry_point = entry_point
            self.nodes = nodes
            self.edges = edges

        async def invoke(self, state: dict) -> dict:
            current = self.entry_point
            data = dict(state)

            while current and current != END:
                node_fn = self.nodes[current]
                result = node_fn(data)
                if inspect.isawaitable(result):
                    result = await result
                if isinstance(result, dict):
                    data.update(result)
                current = self.edges.get(current, END)

            return data

    class StateGraph:
        def __init__(self, _state_type=None):
            self.nodes = {}
            self.edges = {}
            self.entry_point = None

        def add_node(self, name, fn):
            self.nodes[name] = fn

        def add_edge(self, src, dst):
            self.edges[src] = dst

        def set_entry_point(self, name):
            self.entry_point = name

        def compile(self):
            return _CompiledGraph(self.entry_point, self.nodes, self.edges)

    graph_mod.END = END
    graph_mod.StateGraph = StateGraph

    llm_mod = types.ModuleType("spoon_ai.llm")

    class _LLMResponse:
        def __init__(self, content: str):
            self.content = content

    class LLMManager:
        def __init__(self, _config=None):
            self.responder = None

        def set_responder(self, responder):
            """Inject custom responder for deterministic tests."""
            self.responder = responder

        async def chat(self, messages):
            prompt = messages[-1].content if messages else ""
            if callable(self.responder):
                content = self.responder(prompt)
            else:
                content = prompt
            return _LLMResponse(content or "")

    llm_mod.LLMManager = LLMManager
    llm_mod.Response = _LLMResponse

    llm_config_mod = types.ModuleType("spoon_ai.llm.config")

    class ConfigurationManager:
        def __init__(self, *_args, **_kwargs):
            pass

    llm_config_mod.ConfigurationManager = ConfigurationManager

    sys.modules["spoon_ai"] = spoon_ai
    sys.modules["spoon_ai.schema"] = schema
    sys.modules["spoon_ai.graph"] = graph_mod
    sys.modules["spoon_ai.llm"] = llm_mod
    sys.modules["spoon_ai.llm.config"] = llm_config_mod

    spoon_ai.schema = schema
    spoon_ai.graph = graph_mod
    spoon_ai.llm = llm_mod


def _install_faststream_stub() -> None:
    """Stub faststream and NATS broker to avoid real network usage in unit tests."""
    try:
        import importlib

        importlib.import_module("faststream")  # type: ignore
        return
    except Exception:
        pass

    if "faststream" in sys.modules:
        return

    faststream = types.ModuleType("faststream")

    class FastStream:
        def __init__(self, broker):
            self.broker = broker

        async def run(self):
            return None

    faststream.FastStream = FastStream

    nats_mod = types.ModuleType("faststream.nats")

    class NatsBroker:
        def __init__(self, url: str):
            self.url = url
            self.published: list[dict] = []
            self.subscriptions: list[tuple[str, object]] = []

        def subscriber(self, subject: str):
            def decorator(func):
                self.subscriptions.append((subject, func))
                return func

            return decorator

        async def publish(self, message, subject: str):
            self.published.append({"subject": subject, "message": message})

    nats_mod.NatsBroker = NatsBroker

    sys.modules["faststream"] = faststream
    sys.modules["faststream.nats"] = nats_mod
    faststream.nats = nats_mod


def _install_powerdata_stub() -> None:
    """Stub spoon_toolkits crypto tool used for kline data in unit tests."""
    try:
        import importlib

        importlib.import_module("spoon_toolkits")  # type: ignore
        return
    except Exception:
        pass

    if "spoon_toolkits" in sys.modules:
        return

    spoon_toolkits = types.ModuleType("spoon_toolkits")
    crypto_mod = types.ModuleType("spoon_toolkits.crypto")
    powerdata_mod = types.ModuleType("spoon_toolkits.crypto.crypto_powerdata")
    tools_mod = types.ModuleType("spoon_toolkits.crypto.crypto_powerdata.tools")

    class _Result:
        def __init__(self, output=None, error=None):
            self.output = output
            self.error = error

    class CryptoPowerDataCEXTool:
        async def execute(self, **_kwargs):
            return _Result(output={"ohlcv": [1, 2, 3]}, error=None)

    tools_mod.CryptoPowerDataCEXTool = CryptoPowerDataCEXTool

    sys.modules["spoon_toolkits"] = spoon_toolkits
    sys.modules["spoon_toolkits.crypto"] = crypto_mod
    sys.modules["spoon_toolkits.crypto.crypto_powerdata"] = powerdata_mod
    sys.modules["spoon_toolkits.crypto.crypto_powerdata.tools"] = tools_mod

    spoon_toolkits.crypto = crypto_mod
    crypto_mod.crypto_powerdata = powerdata_mod
    powerdata_mod.tools = tools_mod


# Install stubs only if real packages are unavailable
_install_spoon_ai_stub()
_install_faststream_stub()
_install_powerdata_stub()


@pytest.fixture
def settings():
    """Provide Settings with dummy secrets for tests."""
    from spoon_agent.config import Settings

    return Settings()


@pytest.fixture
def reset_main():
    """Reset shared state in spoon_agent.main between unit tests."""
    import spoon_agent.main as main

    class FakeBroker:
        def __init__(self):
            self.published: list[dict] = []

        def subscriber(self, _subject: str):
            def decorator(fn):
                return fn

            return decorator

        async def publish(self, message, subject: str):
            self.published.append({"subject": subject, "message": message})

    main.analysis_graph = None
    main.broker = FakeBroker()

    yield main

    main.analysis_graph = None
    main.broker.published.clear()


@pytest.fixture(autouse=True)
def _silence_spoon_ai_logs():
    """Downgrade noisy spoon_ai logs during tests (cleanup warnings)."""
    logger_names = [
        "spoon_ai.llm.manager",
        "spoon_ai.llm.registry",
        "spoon_ai.llm.config",
        "spoon_ai.llm.providers.openai_compatible_provider",
    ]
    prev_levels = {name: logging.getLogger(name).level for name in logger_names}
    for name in logger_names:
        logging.getLogger(name).setLevel(logging.ERROR)

    yield

    for name, level in prev_levels.items():
        logging.getLogger(name).setLevel(level)


@pytest.fixture(autouse=True)
def _patch_llm_cleanup(monkeypatch):
    """Avoid verbose cleanup warnings from LLMManager for unconfigured providers."""
    from spoon_ai.llm import manager as llm_manager

    monkeypatch.setattr(llm_manager.LLMManager, "_register_cleanup", lambda self: None, raising=False)
    monkeypatch.setattr(llm_manager, "cleanup_sync", lambda *_args, **_kwargs: None, raising=False)
    monkeypatch.setattr(llm_manager.LLMManager, "cleanup", lambda self: None, raising=False)
