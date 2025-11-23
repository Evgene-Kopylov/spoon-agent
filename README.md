# Spoon Agent - Cryptocurrency Trading Analysis

Autonomous AI agent for cryptocurrency trading analysis in the Spoon OS ecosystem.

## Overview

Spoon Agent is a modular trading analysis system that combines:
- **Market data** from Binance API
- **News analysis** via Tavily search
- **Technical analysis** using AI models
- **Investment recommendations** based on multi-factor analysis

## Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- API keys for:
  - OpenAI
  - Tavily
  - Binance (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/Evgene-Kopylov/spoon-agent
cd spoon-agent

# Install dependencies
pip install -e .

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

```python
from spoon_agent.main import run_analysis

# Run analysis for specific tokens
result = await run_analysis(
    tokens=["BTC", "ETH", "SOL"],
    analysis_type="comprehensive"
)
print(result)
```

## Use Cases

### Scenario 1: Isolated Testing (Open Source)

Running the agent locally with mocked external dependencies:

```bash
# Run E2E tests with API mocks
pytest tests/e2e/ -v

# Start local development server
docker-compose up --build

# Testing with sample data
python -m spoon_agent.main --tokens BTC,ETH --mock-mode
```

**E2E Testing Note**: Full E2E test (`test_e2e_pipeline.py`) requires complete Manuspect infrastructure including:
- NATS messaging system
- Redis for state management
- insight_worker service
- All services from the main `manuspect-telegram` repository

For isolated testing, use the E2E test mocks in the `tests/e2e/` directory.

### Scenario 2: Production Deployment (Private Modules)

Connecting to private Manuspect infrastructure:

```bash
# Set up production environment
export SPOON_AGENT_ENV=production
export SPOON_OS_API_URL=https://api.manuspect.com
export SPOON_TOOLKITS_URL=https://toolkits.manuspect.com

# Run with production configuration
docker-compose -f docker-compose.prod.yml up
```

## Architecture

```
spoon_agent/
├── adapters/          # External API integrations
│   ├── binance.py     # Market data
│   └── tavily.py      # News search
├── graphs/            # LangGraph workflows
│   ├── trading_analysis.py
│   └── nodes/         # Individual workflow nodes
├── prompts/           # AI prompt templates
└── utils/             # Utility functions
```

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests with API mocks
pytest tests/e2e/
```

### Local Development

```bash
# Start development environment
docker-compose up -d

# Local agent run
python -m spoon_agent.main

# Debug mode with detailed logging
SPOON_AGENT_DEBUG=true python -m spoon_agent.main
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key

# Optional
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET_KEY=your_binance_secret
SPOON_AGENT_DEBUG=false
```

### Production Deployment

For production deployment with private Manuspect modules:

1. Contact the Manuspect team for access
2. Use the production Docker Compose file
3. Set up reverse proxy and SSL
4. Configure monitoring and logging

## API Reference

### Main Analysis Endpoint

```python
await run_analysis(
    tokens: List[str],           # Cryptocurrency symbols
    analysis_type: str = "comprehensive",  # "quick" | "comprehensive"
    timeframe: str = "1d",       # Analysis timeframe
    mock_mode: bool = False      # Use data mocks for testing
) -> AnalysisResult
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Open Source Issues**: GitHub Issues
- **Private Integration**: contact@manuspect.com
- **Documentation**: [docs.manuspect.com](https://docs.manuspect.com)

## Team

- **Evgene Kopylov** - Project Lead
  - Telegram: @evgenekopylov

## Project Links

- **GitHub**: https://github.com/Evgene-Kopylov/spoon-agent
- **YouTube Demo**: Coming soon