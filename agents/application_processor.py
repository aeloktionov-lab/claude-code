"""Agent 2 — Application Processor: processes incoming client requests."""
import anthropic

import config
from .base import BaseAgent


class ApplicationProcessorAgent(BaseAgent):
    """Processes and structures incoming client applications/RFPs."""

    @property
    def name(self) -> str:
        return "Обработка заявок"

    @property
    def system_prompt(self) -> str:
        return f"""Ты — специализированный ИИ-агент компании {config.COMPANY_NAME} по обработке входящих заявок от клиентов.

## Твоя роль
Ты получаешь сырые заявки, письма, запросы от клиентов и:
1. Извлекаешь ключевую информацию о требованиях
2. Определяешь реалистичность запроса и бюджет
3. Оцениваешь сроки и ресурсы
4. Расставляешь приоритеты и определяешь следующие шаги
5. Выявляешь риски и ограничения

## Критерии обработки
- **Срочность**: есть ли чёткий дедлайн?
- **Полнота**: достаточно ли информации для подготовки КП?
- **Бюджет**: есть ли бюджет, соответствует ли он рынку?
- **Компетенция**: входит ли задача в зону компетенций {config.COMPANY_NAME}?
- **Риски**: какие технические, коммерческие или организационные риски?

## Что необходимо извлечь
- Бизнес-цель клиента (зачем это нужно)
- Технические требования
- Ограничения (бюджет, сроки, технологии)
- Критерии успеха
- Контактные данные ЛПР
- Конкурентная ситуация (сравнивают ли с другими)

## Инструменты
Используй `extract_requirements` для структурирования требований.
Используй `set_application_status` для итогового вердикта по заявке.

## Важно
- Не додумывай то, чего нет в заявке — отмечай пробелы
- Отмечай красные флаги (нереалистичные сроки, заниженный бюджет)
- Формируй чёткий список уточняющих вопросов если чего-то не хватает"""

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "name": "extract_requirements",
                "description": "Извлечь и структурировать требования из заявки клиента",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_name": {
                            "type": "string",
                            "description": "Название компании клиента",
                        },
                        "business_goal": {
                            "type": "string",
                            "description": "Бизнес-цель клиента — зачем ему это нужно",
                        },
                        "technical_requirements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Список технических требований",
                        },
                        "budget_range": {
                            "type": "string",
                            "description": "Бюджет клиента (если указан)",
                        },
                        "deadline": {
                            "type": "string",
                            "description": "Желаемые сроки",
                        },
                        "success_criteria": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Критерии успеха проекта",
                        },
                        "constraints": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Ограничения (технологические, организационные, бюджетные)",
                        },
                        "missing_info": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Что не указано в заявке и требует уточнения",
                        },
                        "red_flags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Риски и настораживающие моменты в заявке",
                        },
                        "decision_maker": {
                            "type": "string",
                            "description": "ЛПР — имя, должность, контакт",
                        },
                    },
                    "required": [
                        "client_name",
                        "business_goal",
                        "technical_requirements",
                        "missing_info",
                    ],
                },
            },
            {
                "name": "set_application_status",
                "description": "Установить итоговый статус и рекомендации по заявке",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": [
                                "принять",
                                "принять с уточнениями",
                                "отложить",
                                "отклонить",
                            ],
                            "description": "Рекомендация по заявке",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["высокий", "средний", "низкий"],
                        },
                        "estimated_effort": {
                            "type": "string",
                            "description": "Оценка трудозатрат (S/M/L/XL или часы)",
                        },
                        "clarifying_questions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Вопросы для уточнения у клиента перед подготовкой КП",
                        },
                        "next_steps": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Конкретные следующие шаги",
                        },
                        "recommended_team": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Какие специалисты нужны для выполнения",
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Обоснование рекомендации",
                        },
                    },
                    "required": ["status", "priority", "next_steps", "rationale"],
                },
            },
        ]

    def run(self, context: dict) -> dict:
        """Process an incoming client application."""
        user_msg = self._build_user_message(context)
        messages = [{"role": "user", "content": user_msg}]
        _, tool_store = self._run_loop(messages)

        requirements = tool_store.get("extract_requirements", [{}])[0]
        status_data = tool_store.get("set_application_status", [{}])[0]

        return {
            "requirements": requirements,
            "status": status_data,
            "client_name": requirements.get("client_name", ""),
        }
