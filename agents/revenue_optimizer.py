"""Agent 6 — Revenue Optimizer: analyses pipeline and maximises revenue."""
import anthropic

import config
from .base import BaseAgent


class RevenueOptimizerAgent(BaseAgent):
    """Analyses all deals and recommends revenue optimisation actions."""

    @property
    def name(self) -> str:
        return "Оптимизация выручки"

    @property
    def system_prompt(self) -> str:
        return f"""Ты — стратегический финансовый аналитик компании {config.COMPANY_NAME}, специализирующийся на максимизации выручки.

## Твоя роль
Ты анализируешь весь коммерческий pipeline компании и:
1. Выявляешь узкие места, которые ограничивают рост выручки
2. Определяешь наиболее прибыльные сегменты и продукты
3. Рекомендуешь конкретные действия по увеличению среднего чека
4. Находишь возможности для upsell и cross-sell
5. Оптимизируешь воронку продаж

## Ключевые метрики для анализа
- **Конверсия по этапам воронки**: где теряем клиентов?
- **Средний чек**: как его увеличить?
- **Цикл сделки**: как сократить?
- **LTV / CAC соотношение**: возврат на привлечение
- **Рентабельность по продуктам/сегментам**: что приносит больше денег?

## Стратегии роста выручки
### Увеличение среднего чека
- Пакетные предложения (bundling)
- Premium-версии услуг
- Дополнительные модули и опции
- Расширение команды на проекте

### Сокращение цикла сделки
- Упрощение процесса принятия решения
- Пилотные проекты / пробный период
- Шаблонные договоры и КП

### Upsell / Cross-sell
- Анализ текущих клиентов на доп. потребности
- Система рекомендаций на основе профиля клиента
- Партнёрские предложения

## Инструменты
Используй `analyze_revenue_stream` для каждого источника выручки.
Используй `add_upsell_opportunity` для возможностей upsell.
Используй `set_revenue_strategy` для общей стратегии роста.
Используй `add_bottleneck` для выявленных узких мест.

Давай конкретные, измеримые рекомендации. Каждая рекомендация должна иметь оценку потенциального эффекта."""

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "name": "analyze_revenue_stream",
                "description": "Проанализировать источник/поток выручки",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "stream_name": {
                            "type": "string",
                            "description": "Название источника выручки (продукт, сегмент, канал)",
                        },
                        "current_revenue": {
                            "type": "string",
                            "description": "Текущая выручка (месяц/год)",
                        },
                        "growth_potential": {
                            "type": "string",
                            "enum": ["высокий", "средний", "низкий"],
                        },
                        "profitability": {
                            "type": "string",
                            "enum": ["высокая", "средняя", "низкая", "убыточная"],
                        },
                        "key_issues": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Ключевые проблемы, сдерживающие рост",
                        },
                        "recommended_actions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Конкретные действия для роста этого потока",
                        },
                    },
                    "required": [
                        "stream_name",
                        "growth_potential",
                        "profitability",
                        "recommended_actions",
                    ],
                },
            },
            {
                "name": "add_upsell_opportunity",
                "description": "Добавить возможность увеличения выручки с текущего клиента",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_name": {
                            "type": "string",
                            "description": "Клиент или сегмент клиентов",
                        },
                        "opportunity_type": {
                            "type": "string",
                            "enum": ["upsell", "cross-sell", "renewal", "expansion"],
                        },
                        "description": {
                            "type": "string",
                            "description": "Что именно предложить и почему это нужно клиенту",
                        },
                        "estimated_revenue": {
                            "type": "string",
                            "description": "Оценка дополнительной выручки",
                        },
                        "probability": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "action_required": {
                            "type": "string",
                            "description": "Что нужно сделать для реализации этой возможности",
                        },
                    },
                    "required": [
                        "client_name",
                        "opportunity_type",
                        "description",
                        "estimated_revenue",
                        "probability",
                        "action_required",
                    ],
                },
            },
            {
                "name": "add_bottleneck",
                "description": "Зафиксировать узкое место в воронке продаж или бизнес-процессе",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "stage": {
                            "type": "string",
                            "description": "Этап воронки или процесс",
                        },
                        "issue": {
                            "type": "string",
                            "description": "В чём проблема",
                        },
                        "revenue_impact": {
                            "type": "string",
                            "description": "Сколько выручки теряем из-за этого",
                        },
                        "solution": {
                            "type": "string",
                            "description": "Как устранить это узкое место",
                        },
                        "effort": {
                            "type": "string",
                            "enum": ["быстрая победа", "среднесрочно", "долгосрочно"],
                        },
                    },
                    "required": ["stage", "issue", "solution", "effort"],
                },
            },
            {
                "name": "set_revenue_strategy",
                "description": "Установить итоговую стратегию роста выручки",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "current_revenue_estimate": {
                            "type": "string",
                            "description": "Оценка текущей выручки",
                        },
                        "target_revenue": {
                            "type": "string",
                            "description": "Целевая выручка через 3-6 месяцев",
                        },
                        "growth_pct": {
                            "type": "number",
                            "description": "Потенциальный рост в процентах",
                        },
                        "top_priorities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Топ-3 приоритетных действия с наибольшим эффектом",
                        },
                        "quick_wins": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Быстрые победы — что можно сделать за 2 недели",
                        },
                        "strategic_initiatives": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Стратегические инициативы на 3-6 месяцев",
                        },
                        "kpis": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "KPI для отслеживания прогресса",
                        },
                    },
                    "required": [
                        "target_revenue",
                        "growth_pct",
                        "top_priorities",
                        "quick_wins",
                    ],
                },
            },
        ]

    def run(self, context: dict) -> dict:
        """Analyse pipeline and generate revenue optimisation recommendations."""
        user_msg = self._build_user_message(context)
        messages = [{"role": "user", "content": user_msg}]
        _, tool_store = self._run_loop(messages)

        return {
            "revenue_streams": tool_store.get("analyze_revenue_stream", []),
            "upsell_opportunities": tool_store.get("add_upsell_opportunity", []),
            "bottlenecks": tool_store.get("add_bottleneck", []),
            "strategy": tool_store.get("set_revenue_strategy", [{}])[0],
        }
