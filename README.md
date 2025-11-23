# Spoon Agent - Анализ криптовалютных торгов

Автономный AI-агент для анализа криптовалютных торгов в экосистеме Spoon OS.

## Обзор

Spoon Agent - это модульная система анализа торгов, которая объединяет:
- **Рыночные данные** из Binance API
- **Анализ новостей** через Tavily search
- **Технический анализ** с использованием AI моделей
- **Инвестиционные рекомендации** на основе многофакторного анализа

## Быстрый старт

### Предварительные требования
- Python 3.12+
- Docker & Docker Compose
- API ключи для:
  - OpenAI
  - Tavily
  - Binance (опционально)

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/manuspect/spoon-agent
cd spoon-agent

# Установить зависимости
pip install -e .

# Скопировать шаблон окружения
cp .env.example .env
# Отредактировать .env с вашими API ключами
```

### Базовое использование

```python
from spoon_agent.main import run_analysis

# Запустить анализ для конкретных токенов
result = await run_analysis(
    tokens=["BTC", "ETH", "SOL"],
    analysis_type="comprehensive"
)
print(result)
```

## Сценарии использования

### Сценарий 1: Изолированное тестирование (Open Source)

Запуск агента локально с моками внешних зависимостей:

```bash
# Запуск E2E тестов с моками API
pytest tests/e2e/ -v

# Запуск локального сервера разработки
docker-compose up --build

# Тестирование с примерными данными
python -m spoon_agent.main --tokens BTC,ETH --mock-mode
```

**Примечание по E2E тестированию**: Полный E2E тест (`test_e2e_pipeline.py`) требует полной инфраструктуры Manuspect включая:
- NATS messaging system
- Redis для управления состоянием
- insight_worker сервис
- Все сервисы из основного репозитория `manuspect-telegram`

Для изолированного тестирования используйте моки E2E тестов в директории `tests/e2e/`.

### Сценарий 2: Продакшен развертывание (Приватные модули)

Подключение к приватной инфраструктуре Manuspect:

```bash
# Установка продакшен окружения
export SPOON_AGENT_ENV=production
export SPOON_OS_API_URL=https://api.manuspect.com
export SPOON_TOOLKITS_URL=https://toolkits.manuspect.com

# Запуск с продакшен конфигурацией
docker-compose -f docker-compose.prod.yml up
```

## Архитектура

```
spoon_agent/
├── adapters/          # Интеграции с внешними API
│   ├── binance.py     # Рыночные данные
│   └── tavily.py      # Поиск новостей
├── graphs/            # LangGraph workflows
│   ├── trading_analysis.py
│   └── nodes/         # Отдельные узлы workflow
├── prompts/           # Шаблоны AI промптов
└── utils/             # Вспомогательные функции
```

## Разработка

### Запуск тестов

```bash
# Юнит тесты
pytest tests/unit/

# Интеграционные тесты
pytest tests/integration/

# E2E тесты с моками API
pytest tests/e2e/
```

### Локальная разработка

```bash
# Запуск среды разработки
docker-compose up -d

# Локальный запуск агента
python -m spoon_agent.main

# Режим отладки с подробным логированием
SPOON_AGENT_DEBUG=true python -m spoon_agent.main
```

## Конфигурация

### Переменные окружения

```bash
# Обязательные
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key

# Опциональные
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET_KEY=your_binance_secret
SPOON_AGENT_DEBUG=false
```

### Продакшен развертывание

Для продакшен развертывания с приватными модулями Manuspect:

1. Свяжитесь с командой Manuspect для получения доступа
2. Используйте продакшен Docker Compose файл
3. Настройте reverse proxy и SSL
4. Настройте мониторинг и логирование

## API Reference

### Основной эндпоинт анализа

```python
await run_analysis(
    tokens: List[str],           # Символы криптовалют
    analysis_type: str = "comprehensive",  # "quick" | "comprehensive"
    timeframe: str = "1d",       # Временной интервал анализа
    mock_mode: bool = False      # Использовать моки данных для тестирования
) -> AnalysisResult
```

## Вклад в проект

1. Форкните репозиторий
2. Создайте ветку фичи (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Запушьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## Лицензия

Этот проект лицензирован под MIT License - смотрите файл LICENSE для деталей.

## Поддержка

- **Проблемы Open Source**: GitHub Issues
- **Приватная интеграция**: contact@manuspect.com
- **Документация**: [docs.manuspect.com](https://docs.manuspect.com)