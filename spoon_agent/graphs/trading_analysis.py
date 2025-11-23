"""Trading lead analysis graph for cryptocurrency market analysis."""

import logging
from typing import Any, Optional, TypedDict

from spoon_ai.graph import END, StateGraph
from spoon_ai.llm import LLMManager
from spoon_ai.llm.config import ConfigurationManager
from spoon_toolkits.crypto.crypto_powerdata.tools import CryptoPowerDataCEXTool

from spoon_agent.adapters.tavily import TavilyAdapter
from spoon_agent.config import Settings
from spoon_agent.graphs.nodes.extraction import extract_coins_from_messages
from spoon_agent.graphs.nodes.data_fetching import fetch_binance_data, prepare_token_list
from spoon_agent.graphs.nodes.token_analysis import analyze_token
from spoon_agent.graphs.nodes.aggregation import aggregate_results

logger = logging.getLogger(__name__)


class TradingAnalysisState(TypedDict, total=False):
    """State for trading lead analysis graph."""

    # Input fields
    chat_id: str
    sender_id: str
    reasoning: str
    messages: list[str]
    task_type: str

    # Extraction
    extracted_coins: list[str]
    coin_extraction_method: str
    extraction_log: list[str]

    # Market data
    binance_market_data: dict[str, Any]
    selected_tokens: list[str]
    token_details: dict[str, dict]

    # Analysis
    token_reports: dict[str, dict]
    token_scores: dict[str, float]

    # Final output
    final_summary: str

    # Metadata
    execution_log: list[str]
    error: Optional[str]


class TradingAnalysisGraph:
    """Graph for analyzing trading leads with crypto market analysis."""

    MAX_PARALLEL_TOKENS = 5  # Maximum tokens to analyze in parallel

    def __init__(self, settings: Settings):
        """
        Initialize trading analysis graph.

        Args:
            settings: Application settings
        """
        self.settings = settings

        # Initialize LLM manager with configuration
        config_manager = ConfigurationManager()
        self.llm = LLMManager(config_manager)

        self.graph = None

        # Initialize tools
        self.powerdata_tool = CryptoPowerDataCEXTool()
        self.tavily_adapter = TavilyAdapter(
            api=None,
            api_key=settings.tavily_api_key
        )

    async def initialize(self) -> None:
        """Initialize graph and external tools."""
        # Initialize Tavily adapter
        await self.tavily_adapter.initialize()

        # Build graph
        self._build_graph()

        logger.info("Trading analysis graph initialized")

    def _build_graph(self) -> None:
        """Build graph for trading analysis using StateGraph API."""

        # Create graph with state schema
        graph = StateGraph(TradingAnalysisState)

        # Add sequential nodes
        graph.add_node("extract_coins", self._extract_coins)
        graph.add_node("fetch_binance_data", fetch_binance_data)
        graph.add_node("prepare_token_list", prepare_token_list)

        # Add token analysis node (handles parallel processing internally)
        graph.add_node("analyze_tokens", self._analyze_all_tokens)

        # Add aggregation node
        graph.add_node("aggregate_results", self._aggregate_results)

        # Define edges
        graph.add_edge("extract_coins", "fetch_binance_data")
        graph.add_edge("fetch_binance_data", "prepare_token_list")
        graph.add_edge("prepare_token_list", "analyze_tokens")
        graph.add_edge("analyze_tokens", "aggregate_results")
        graph.add_edge("aggregate_results", END)

        # Set entry point
        graph.set_entry_point("extract_coins")

        # Compile graph
        self.graph = graph.compile()

        logger.info("Graph built successfully")

    async def _extract_coins(self, state: TradingAnalysisState) -> dict[str, Any]:
        """
        Wrapper for coin extraction node.

        Args:
            state: Current graph state

        Returns:
            Updated state with extracted coins
        """
        return await extract_coins_from_messages(
            state,
            llm=self.llm,
            default_coins=self.settings.default_popular_coins
        )

    async def _aggregate_results(self, state: TradingAnalysisState) -> dict[str, Any]:
        """
        Wrapper for aggregation node.

        Args:
            state: Current graph state

        Returns:
            Updated state with final summary
        """
        return await aggregate_results(state, llm=self.llm)

    async def _analyze_all_tokens(
        self,
        state: TradingAnalysisState
    ) -> dict[str, Any]:
        """
        Analyze all tokens in parallel (up to MAX_PARALLEL_TOKENS).

        Args:
            state: Current graph state

        Returns:
            Updated state with all token analyses
        """
        import asyncio

        selected_tokens = state.get("selected_tokens", [])

        if not selected_tokens:
            logger.warning("No tokens to analyze")
            return {"token_reports": {}, "token_scores": {}}

        # Limit to MAX_PARALLEL_TOKENS
        tokens_to_analyze = selected_tokens[:self.MAX_PARALLEL_TOKENS]

        logger.info(f"Analyzing {len(tokens_to_analyze)} tokens in parallel")

        # Analyze all tokens in parallel
        tasks = [
            analyze_token(
                token=token,
                state=state,
                llm=self.llm,
                powerdata_tool=self.powerdata_tool,
                tavily_adapter=self.tavily_adapter
            )
            for token in tokens_to_analyze
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results
        token_reports = (state.get("token_reports") or {}).copy()
        token_scores = (state.get("token_scores") or {}).copy()

        for token, result in zip(tokens_to_analyze, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to analyze {token}: {result}")
                continue

            if isinstance(result, dict):
                # Merge token_reports
                if "token_reports" in result:
                    token_reports.update(result["token_reports"])
                # Merge token_scores
                if "token_scores" in result:
                    token_scores.update(result["token_scores"])

        return {
            "token_reports": token_reports,
            "token_scores": token_scores
        }

    async def run(
        self,
        chat_id: str,
        sender_id: str,
        reasoning: str,
        messages: list[str],
        task_type: str = "trading_lead_analysis"
    ) -> dict[str, Any]:
        """
        Run trading lead analysis.

        Args:
            chat_id: Telegram chat ID
            sender_id: Telegram user ID (sender)
            reasoning: Reasoning why this is a potential client
            messages: List of messages from sender
            task_type: Task type identifier

        Returns:
            Analysis result with final_summary field
        """
        if not self.graph:
            await self.initialize()

        # Initial state
        initial_state: TradingAnalysisState = {
            "chat_id": chat_id,
            "sender_id": sender_id,
            "reasoning": reasoning,
            "messages": messages,
            "task_type": task_type,
            "execution_log": []
        }

        logger.info(f"Running analysis for sender {sender_id} with {len(messages)} messages")

        # Execute graph
        try:
            result = await self.graph.invoke(initial_state)
            logger.info("Analysis completed successfully")
            return result

        except Exception as exc:
            logger.error(f"Analysis failed: {exc}")
            return {
                "error": str(exc),
                "final_summary": f"Анализ завершился с ошибкой: {exc}"
            }
