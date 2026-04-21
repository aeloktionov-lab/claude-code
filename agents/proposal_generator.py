"""Agent 4 — Proposal Generator: creates commercial proposals (КП)."""
import anthropic

import config
from .base import BaseAgent


class ProposalGeneratorAgent(BaseAgent):
    """Generates tailored commercial proposals (КП) for clients."""

    @property
    def name(self) -> str:
        return "Подготовка КП"

    @property
    def system_prompt(self) -> str:
        return f"""Ты — ведущий специалист компании {config.COMPANY_NAME} по подготовке коммерческих предложений (КП).

## Твоя роль
Ты создаёшь убедительные, персонализированные коммерческие предложения, которые:
1. Чётко отвечают на боль клиента
2. Демонстрируют ценность, а не просто цену
3. Выгодно выделяют {config.COMPANY_NAME} на фоне конкурентов
4. Содержат чёткий призыв к действию
5. Снимают типичные возражения клиента

## Структура КП (AIDA-модель)
1. **Заголовок**: персонализированный, о результате для клиента
2. **Резюме**: ключевая ценность за 3 предложения (Executive Summary)
3. **Понимание задачи**: покажи, что понял бизнес-контекст клиента
4. **Наше решение**: описание подхода, методологии, команды
5. **Почему мы**: УТП, кейсы, доказательства экспертизы
6. **План работ**: этапы, сроки, deliverables
7. **Стоимость**: прозрачное ценообразование с вариантами
8. **Следующий шаг**: конкретный и лёгкий призыв к действию
9. **Условия**: гарантии, SLA, условия оплаты

## Принципы убедительного КП
- Говори о результатах клиента, не о своих технологиях
- Используй конкретные цифры и метрики
- Снимай страхи: гарантии, поэтапность, фиксированная цена
- Создавай срочность: ограниченный слот, акция, дедлайн
- Персонализируй: упоминай детали из заявки клиента

## Инструменты
Используй `add_proposal_section` для каждого раздела КП.
Используй `set_proposal_meta` для метаданных и ключевых показателей КП.

Пиши на живом, профессиональном русском языке. Избегай канцелярита и шаблонных фраз."""

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "name": "add_proposal_section",
                "description": "Добавить раздел коммерческого предложения",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "section_name": {
                            "type": "string",
                            "description": "Название раздела КП",
                        },
                        "order": {
                            "type": "integer",
                            "description": "Порядковый номер раздела (1, 2, 3...)",
                        },
                        "content": {
                            "type": "string",
                            "description": "Содержание раздела (markdown-форматирование приветствуется)",
                        },
                        "key_message": {
                            "type": "string",
                            "description": "Главное сообщение этого раздела в одном предложении",
                        },
                    },
                    "required": ["section_name", "order", "content"],
                },
            },
            {
                "name": "set_proposal_meta",
                "description": "Установить метаданные и ключевые показатели КП",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "proposal_title": {
                            "type": "string",
                            "description": "Заголовок КП",
                        },
                        "client_name": {
                            "type": "string",
                            "description": "Название компании клиента",
                        },
                        "total_price": {
                            "type": "string",
                            "description": "Итоговая стоимость (может быть диапазон)",
                        },
                        "timeline": {
                            "type": "string",
                            "description": "Общие сроки реализации",
                        },
                        "payment_terms": {
                            "type": "string",
                            "description": "Условия оплаты",
                        },
                        "key_value_propositions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "3-5 ключевых преимуществ для клиента",
                        },
                        "objection_handlers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Как мы снимаем типичные возражения",
                        },
                        "call_to_action": {
                            "type": "string",
                            "description": "Конкретный следующий шаг для клиента",
                        },
                        "valid_until": {
                            "type": "string",
                            "description": "До какой даты действует КП",
                        },
                        "discount_offer": {
                            "type": "string",
                            "description": "Специальное предложение / скидка (если есть)",
                        },
                    },
                    "required": [
                        "proposal_title",
                        "client_name",
                        "total_price",
                        "timeline",
                        "key_value_propositions",
                        "call_to_action",
                    ],
                },
            },
        ]

    def run(self, context: dict) -> dict:
        """Generate a commercial proposal based on client context and pricing."""
        user_msg = self._build_user_message(context)
        messages = [{"role": "user", "content": user_msg}]
        _, tool_store = self._run_loop(messages)

        sections = sorted(
            tool_store.get("add_proposal_section", []),
            key=lambda s: s.get("order", 99),
        )
        meta = tool_store.get("set_proposal_meta", [{}])[0]

        return {
            "sections": sections,
            "meta": meta,
            "section_count": len(sections),
        }
