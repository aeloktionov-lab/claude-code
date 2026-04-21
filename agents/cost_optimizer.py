"""Agent 3 — Cost Optimizer: calculates and optimises project cost price."""
import anthropic

import config
from .base import BaseAgent


class CostOptimizerAgent(BaseAgent):
    """Calculates cost price (себестоимость) and optimises margins."""

    @property
    def name(self) -> str:
        return "Оптимизация себестоимости"

    @property
    def system_prompt(self) -> str:
        return f"""Ты — финансовый ИИ-аналитик компании {config.COMPANY_NAME}, специализирующийся на расчёте и оптимизации себестоимости проектов.

## Твоя роль
Ты получаешь описание проекта или заявки и:
1. Рассчитываешь детальную себестоимость по статьям
2. Определяешь оптимальную маржу и итоговую цену для клиента
3. Находишь возможности снижения себестоимости без потери качества
4. Оцениваешь финансовые риски

## Статьи себестоимости
- **Прямые затраты**: ФОТ (фонд оплаты труда) с учётом налогов, подрядчики
- **Лицензии и ПО**: инструменты, библиотеки, сервисы
- **Инфраструктура**: серверы, облачные сервисы, хостинг
- **Управление**: PM, аналитики, QA
- **Буфер рисков**: 10-20% от прямых затрат
- **Накладные расходы**: офис, коммуникации, поддержка

## Принципы ценообразования
- Целевая маржа: 30-50% от себестоимости (зависит от конкуренции)
- Для стратегических клиентов допустима маржа 15-25%
- При высоком риске — закладывай буфер 20-30%
- Учитывай стоимость привлечения клиента (CAC) и LTV

## Оптимизация
- Стандартизация и переиспользование компонентов
- Автоматизация рутинных задач
- Субподряд на не-ключевые работы
- Поэтапная разбивка (снижает риск для обеих сторон)
- Ценообразование на основе ценности (Value-based), а не только затрат

## Инструменты
Используй `add_cost_item` для каждой статьи затрат.
Используй `set_pricing` для итогового ценового предложения.
Используй `add_optimization` для каждой возможности оптимизации.

Оперируй реалистичными рыночными ставками. При отсутствии данных — указывай диапазоны."""

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "name": "add_cost_item",
                "description": "Добавить статью затрат в расчёт себестоимости",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": [
                                "ФОТ",
                                "Подрядчики",
                                "Лицензии и ПО",
                                "Инфраструктура",
                                "Управление",
                                "Буфер рисков",
                                "Накладные расходы",
                                "Прочее",
                            ],
                        },
                        "item_name": {
                            "type": "string",
                            "description": "Наименование статьи затрат",
                        },
                        "amount_min": {
                            "type": "number",
                            "description": "Минимальная сумма в рублях",
                        },
                        "amount_max": {
                            "type": "number",
                            "description": "Максимальная сумма в рублях",
                        },
                        "description": {
                            "type": "string",
                            "description": "Детализация: из чего складывается эта сумма",
                        },
                    },
                    "required": ["category", "item_name", "amount_min", "amount_max"],
                },
            },
            {
                "name": "add_optimization",
                "description": "Добавить возможность оптимизации себестоимости",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "opportunity": {
                            "type": "string",
                            "description": "Описание возможности снижения затрат",
                        },
                        "potential_saving_pct": {
                            "type": "number",
                            "description": "Потенциальная экономия в процентах",
                        },
                        "implementation_effort": {
                            "type": "string",
                            "enum": ["низкий", "средний", "высокий"],
                            "description": "Сложность внедрения оптимизации",
                        },
                        "tradeoffs": {
                            "type": "string",
                            "description": "На что влияет эта оптимизация (риски, качество, сроки)",
                        },
                    },
                    "required": ["opportunity", "potential_saving_pct", "implementation_effort"],
                },
            },
            {
                "name": "set_pricing",
                "description": "Установить итоговое ценовое предложение",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "cost_price_min": {
                            "type": "number",
                            "description": "Себестоимость — минимум (руб.)",
                        },
                        "cost_price_max": {
                            "type": "number",
                            "description": "Себестоимость — максимум (руб.)",
                        },
                        "recommended_price": {
                            "type": "number",
                            "description": "Рекомендуемая цена для клиента (руб.)",
                        },
                        "price_range_min": {
                            "type": "number",
                            "description": "Минимально допустимая цена (руб.)",
                        },
                        "price_range_max": {
                            "type": "number",
                            "description": "Максимально обоснованная цена (руб.)",
                        },
                        "margin_pct": {
                            "type": "number",
                            "description": "Маржа при рекомендуемой цене (%)",
                        },
                        "pricing_strategy": {
                            "type": "string",
                            "enum": [
                                "фиксированная цена",
                                "time & material",
                                "поэтапная оплата",
                                "подписка",
                                "смешанная",
                            ],
                        },
                        "payment_terms": {
                            "type": "string",
                            "description": "Рекомендуемые условия оплаты",
                        },
                        "financial_risks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Финансовые риски проекта",
                        },
                    },
                    "required": [
                        "cost_price_min",
                        "cost_price_max",
                        "recommended_price",
                        "margin_pct",
                        "pricing_strategy",
                    ],
                },
            },
        ]

    def run(self, context: dict) -> dict:
        """Calculate cost price and optimal pricing for a project."""
        user_msg = self._build_user_message(context)
        messages = [{"role": "user", "content": user_msg}]
        _, tool_store = self._run_loop(messages)

        cost_items = tool_store.get("add_cost_item", [])
        optimizations = tool_store.get("add_optimization", [])
        pricing = tool_store.get("set_pricing", [{}])[0]

        return {
            "cost_items": cost_items,
            "optimizations": optimizations,
            "pricing": pricing,
            "total_cost_items": len(cost_items),
        }
