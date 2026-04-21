"""Agent 5 — Client Retention: analyses churn risk and re-engages clients."""
import anthropic

import config
from .base import BaseAgent


class ClientRetentionAgent(BaseAgent):
    """Analyses client health and generates retention / re-engagement strategies."""

    @property
    def name(self) -> str:
        return "Возврат клиентов"

    @property
    def system_prompt(self) -> str:
        return f"""Ты — специалист по удержанию и возврату клиентов компании {config.COMPANY_NAME}.

## Твоя роль
Ты анализируешь данные о клиентах и:
1. Оцениваешь риск оттока (churn score)
2. Выявляешь причины снижения активности или ухода
3. Разрабатываешь персонализированные стратегии возврата
4. Создаёшь конкретные скрипты и сообщения для реактивации

## Классификация клиентов по риску
- **Критический (80-100%)**: нет контакта 3+ месяца, жалобы, ушёл к конкуренту
- **Высокий (60-79%)**: снижение объёма, задержка платежей, холодные отклики
- **Средний (40-59%)**: редкие покупки, нейтральные отклики, нет развития
- **Низкий (0-39%)**: регулярный клиент, позитивная обратная связь

## Стратегии возврата
### Win-back кампания
- Персональное письмо от ТОП-менеджера
- Специальное предложение (скидка, бонус, пилот)
- Демонстрация улучшений с момента ухода

### Реактивация «спящих» клиентов
- Напоминание о ценности (case study, результаты)
- Новые продукты/услуги, которые решают их текущие боли
- Приглашение на мероприятие / демо

### Удержание «под угрозой»
- Экстренная встреча / звонок
- Индивидуальный план улучшений
- Назначение персонального менеджера

## Инструменты
Используй `analyze_client` для оценки каждого клиента.
Используй `create_retention_action` для конкретных шагов возврата.
Используй `write_reactivation_message` для готового текста реактивационного сообщения.

Будь эмпатичным, но конкретным. Каждый план должен быть реалистичным и исполнимым."""

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "name": "analyze_client",
                "description": "Проанализировать состояние клиента и оценить риск оттока",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_name": {"type": "string"},
                        "churn_score": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Вероятность оттока в процентах",
                        },
                        "risk_level": {
                            "type": "string",
                            "enum": ["критический", "высокий", "средний", "низкий"],
                        },
                        "last_contact": {
                            "type": "string",
                            "description": "Когда был последний контакт",
                        },
                        "revenue_trend": {
                            "type": "string",
                            "enum": ["растёт", "стабильно", "снижается", "нет выручки"],
                        },
                        "churn_reasons": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Предполагаемые причины оттока / снижения активности",
                        },
                        "client_ltv": {
                            "type": "string",
                            "description": "LTV клиента (фактическая или потенциальная выручка)",
                        },
                        "retention_priority": {
                            "type": "string",
                            "enum": ["приоритет 1", "приоритет 2", "приоритет 3"],
                        },
                    },
                    "required": [
                        "client_name",
                        "churn_score",
                        "risk_level",
                        "churn_reasons",
                        "retention_priority",
                    ],
                },
            },
            {
                "name": "create_retention_action",
                "description": "Создать конкретное действие по удержанию / возврату клиента",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_name": {"type": "string"},
                        "action_type": {
                            "type": "string",
                            "enum": [
                                "звонок",
                                "письмо",
                                "встреча",
                                "специальное предложение",
                                "демо/презентация",
                                "передача менеджеру",
                            ],
                        },
                        "timing": {
                            "type": "string",
                            "description": "Когда нужно выполнить это действие",
                        },
                        "responsible": {
                            "type": "string",
                            "description": "Кто отвечает (роль)",
                        },
                        "description": {
                            "type": "string",
                            "description": "Что именно нужно сделать",
                        },
                        "offer_details": {
                            "type": "string",
                            "description": "Детали специального предложения (если есть)",
                        },
                        "success_metric": {
                            "type": "string",
                            "description": "Как поймём, что действие успешно",
                        },
                    },
                    "required": [
                        "client_name",
                        "action_type",
                        "timing",
                        "description",
                    ],
                },
            },
            {
                "name": "write_reactivation_message",
                "description": "Написать готовый текст письма / сообщения для реактивации клиента",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_name": {"type": "string"},
                        "channel": {
                            "type": "string",
                            "enum": ["email", "telegram", "whatsapp", "звонок — скрипт"],
                        },
                        "subject": {
                            "type": "string",
                            "description": "Тема письма / первая фраза сообщения",
                        },
                        "message_text": {
                            "type": "string",
                            "description": "Полный текст сообщения (готов к отправке)",
                        },
                        "tone": {
                            "type": "string",
                            "enum": ["деловой", "дружеский", "срочный", "заботливый"],
                        },
                    },
                    "required": ["client_name", "channel", "subject", "message_text"],
                },
            },
        ]

    def run(self, context: dict) -> dict:
        """Analyse clients and generate retention actions."""
        user_msg = self._build_user_message(context)
        messages = [{"role": "user", "content": user_msg}]
        _, tool_store = self._run_loop(messages)

        analyses = tool_store.get("analyze_client", [])
        actions = tool_store.get("create_retention_action", [])
        messages_out = tool_store.get("write_reactivation_message", [])

        return {
            "client_analyses": analyses,
            "retention_actions": actions,
            "reactivation_messages": messages_out,
            "clients_analyzed": len(analyses),
        }
