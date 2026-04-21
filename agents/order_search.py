"""Agent 1 — Order Search: finds and scores potential orders/leads."""
import anthropic

import config
from .base import BaseAgent


class OrderSearchAgent(BaseAgent):
    """Searches for potential orders and qualifies leads for CROID."""

    @property
    def name(self) -> str:
        return "Поиск заказов"

    @property
    def system_prompt(self) -> str:
        return f"""Ты — специализированный ИИ-агент компании {config.COMPANY_NAME} по поиску и квалификации потенциальных заказов.

## Твоя роль
Ты анализируешь рыночную информацию, данные о клиентах и бизнес-контекст, чтобы:
1. Выявить перспективные лиды и потенциальные заказы
2. Оценить вероятность успешной сделки (0-100%)
3. Расставить приоритеты по ценности и срочности
4. Предложить конкретные следующие шаги для каждого лида

## Критерии квалификации лида
- **Высокий приоритет**: бюджет подтверждён, ЛПР определён, потребность срочная
- **Средний приоритет**: бюджет ориентировочный, выход на ЛПР возможен, потребность актуальна
- **Низкий приоритет**: бюджет не определён, контакт с ЛПР не установлен

## Метрики оценки
- Соответствие профилю идеального клиента
- Размер потенциальной сделки
- Длина цикла продаж
- Конкурентная ситуация
- Готовность к покупке

## Твои инструменты
Используй `add_lead` для каждого выявленного лида. Используй `set_search_summary` в конце для итоговой сводки.

## Формат работы
1. Проанализируй входящий контекст
2. Для каждого потенциального лида вызови `add_lead`
3. Предложи стратегию работы с лидами
4. Вызови `set_search_summary` с общим итогом
5. Напиши краткое резюме своих выводов

Отвечай профессионально, конкретно и actionable. Все выводы должны быть обоснованы данными из контекста."""

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "name": "add_lead",
                "description": "Добавить квалифицированный лид в список потенциальных заказов",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Название компании-потенциального клиента",
                        },
                        "contact_person": {
                            "type": "string",
                            "description": "ФИО и должность контактного лица / ЛПР",
                        },
                        "segment": {
                            "type": "string",
                            "description": "Отраслевой сегмент (IT, ритейл, производство и т.д.)",
                        },
                        "estimated_budget": {
                            "type": "string",
                            "description": "Ориентировочный бюджет сделки (например: 500 000 - 1 000 000 руб.)",
                        },
                        "probability": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Вероятность закрытия сделки в процентах",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["высокий", "средний", "низкий"],
                            "description": "Приоритет лида",
                        },
                        "pain_points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Ключевые боли и потребности клиента",
                        },
                        "next_action": {
                            "type": "string",
                            "description": "Конкретное следующее действие (звонок, встреча, отправить КП)",
                        },
                        "timeline": {
                            "type": "string",
                            "description": "Ожидаемые сроки принятия решения",
                        },
                        "competitors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Конкуренты, которые также претендуют на этот заказ",
                        },
                    },
                    "required": [
                        "company_name",
                        "segment",
                        "estimated_budget",
                        "probability",
                        "priority",
                        "next_action",
                    ],
                },
            },
            {
                "name": "set_search_summary",
                "description": "Установить итоговое резюме поиска заказов",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "total_leads": {
                            "type": "integer",
                            "description": "Общее количество найденных лидов",
                        },
                        "total_potential_revenue": {
                            "type": "string",
                            "description": "Суммарный потенциальный доход (диапазон)",
                        },
                        "top_opportunity": {
                            "type": "string",
                            "description": "Наиболее перспективная возможность",
                        },
                        "recommended_focus": {
                            "type": "string",
                            "description": "На каком сегменте или лиде сосредоточить усилия в первую очередь",
                        },
                        "strategy": {
                            "type": "string",
                            "description": "Краткая стратегия работы с найденными лидами",
                        },
                    },
                    "required": [
                        "total_leads",
                        "total_potential_revenue",
                        "recommended_focus",
                        "strategy",
                    ],
                },
            },
        ]

    def run(self, context: dict) -> dict:
        """Find and qualify leads from the provided market context."""
        user_msg = self._build_user_message(context)
        messages = [{"role": "user", "content": user_msg}]
        _, tool_store = self._run_loop(messages)

        leads = tool_store.get("add_lead", [])
        summary = tool_store.get("set_search_summary", [{}])[0]

        return {
            "leads": leads,
            "summary": summary,
            "lead_count": len(leads),
        }
