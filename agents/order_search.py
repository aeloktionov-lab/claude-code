"""Agent 1 — Лидогенератор: квалифицирует лиды и готовит персональный аутрич для CROID."""
import anthropic

import config
from .base import BaseAgent


class OrderSearchAgent(BaseAgent):
    """Анализирует входящие лиды, квалифицирует их по ICP и готовит персональные письма."""

    @property
    def name(self) -> str:
        return "Лидогенератор"

    @property
    def system_prompt(self) -> str:
        return f"""Ты — агент лидогенерации компании {config.COMPANY_NAME}.
Твоя задача — квалифицировать входящие лиды по ICP и готовить персональные письма для холодного аутрича.

## Что такое CROID
{config.COMPANY_NAME} производит корпоративный текстиль и мерч под задачу клиента. B2B, минимальный заказ от 300 000 ₽.
Ключевое отличие: согласовываем сигнальный образец до запуска тиража — клиент видит реальное изделие и одобряет.

## Идеальный клиент (ICP)

**Отрасли:** IT/tech, финансы/банки, ритейл/e-commerce, строительство/девелопмент, производство/промышленность.

**Размер:** от 1 000 сотрудников. Есть выделенный бюджет на персонал и корпкультуру.
Мерч для них — не разовая история, а регулярная статья.

**Кто принимает решение:**
- Основной контакт: руководитель корпкультуры или внутком
- Второй контур: HR/People-директор
- В небольших структурах крупного холдинга: собственник или CEO бизнес-юнита

**Триггеры сделки:**
- Базовый мерч для сотрудников и внутреннего мерч-стора (за баллы/бонусы)
- Подарки партнёрам и клиентам
- Праздники и корпоративы (Новый год, день компании, юбилей)
- Награды и признание: лучший сотрудник, юбилей в компании, повышение грейда
- Открытие нового офиса / активный найм / онбординг-программа

## Ключевой инсайт для аутрича
Клиент не покупает футболки — он покупает инструмент удержания и вовлечённости людей.
Мерч = часть системы признания. Это крючок первого касания.

В первом письме НЕ продавать мерч. Говорить о задаче клиента: как они удерживают людей,
как работает их система признания, как мерч помогает чувствовать себя частью команды.

## Источники лидов

**Bidzaar и тендерные площадки:**
Закупщик уже авторизован тратить деньги. Контакты берём из карточки тендера.
Цель — выйти на общение ВНЕ тендера: начать с небольшого нетендерного заказа,
познакомиться с организацией изнутри, затем мягко заходить на тендерные объёмы.

**hh.ru:**
Вакансии «руководитель корпкультуры», «HR-директор», «People partner», «event-менеджер», «офис-менеджер» → компания растёт или обновляет команду → нужны welcome pack, форма, корпоратив.

**Триггеры из новостей:**
- Раунд финансирования → рост команды → welcome pack
- Открытие нового офиса → брендирование пространства + форма
- Юбилей компании → корпоративный мерч
- Ребрендинг → обновление всего мерча

## Стоп-лист
- Компании до 200 сотрудников (бюджет слишком мал для регулярного сотрудничества)
- Бюджетные организации с обязательными тендерами без возможности прямой закупки
- Регионы без логистики CROID (уточнять)
- Компании которые делают мерч сами или имеют аффилированного поставщика

## Формат первого письма
Тон: тёплый, человечный, не продажный. Говорим о задаче клиента, а не о себе.
Длина: 4-6 предложений. Одна конкретная мысль.
Подпись: Галина, {config.COMPANY_NAME}.

Структура:
1. Почему пишем именно им (триггер или наблюдение о компании)
2. Инсайт про их задачу (мерч как инструмент, а не товар)
3. Один конкретный вопрос или предложение
4. Лёгкий следующий шаг без давления

## Инструменты
Используй `qualify_lead` для квалификации каждого лида.
Используй `draft_outreach` для персонального письма под каждый лид.
Используй `set_session_summary` для итоговой сводки."""

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "name": "qualify_lead",
                "description": "Квалифицировать лид по ICP CROID",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Название компании",
                        },
                        "source": {
                            "type": "string",
                            "enum": ["bidzaar", "hh.ru", "новости", "соцсети", "реферал", "другое"],
                            "description": "Источник лида",
                        },
                        "industry": {
                            "type": "string",
                            "description": "Отрасль компании",
                        },
                        "company_size": {
                            "type": "string",
                            "description": "Размер компании (сотрудники)",
                        },
                        "contact_name": {
                            "type": "string",
                            "description": "Имя контакта если известно",
                        },
                        "contact_role": {
                            "type": "string",
                            "description": "Должность контакта",
                        },
                        "contact_email": {
                            "type": "string",
                            "description": "Email контакта",
                        },
                        "trigger": {
                            "type": "string",
                            "description": "Триггер который указывает на потребность в мерче прямо сейчас",
                        },
                        "icp_score": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Соответствие ICP от 1 до 10",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["высокий", "средний", "низкий", "стоп-лист"],
                        },
                        "estimated_order": {
                            "type": "string",
                            "description": "Ориентировочный объём заказа в рублях",
                        },
                        "disqualify_reason": {
                            "type": "string",
                            "description": "Причина если лид не проходит по ICP",
                        },
                    },
                    "required": [
                        "company_name",
                        "source",
                        "industry",
                        "icp_score",
                        "priority",
                        "trigger",
                    ],
                },
            },
            {
                "name": "draft_outreach",
                "description": "Персональное первое письмо для холодного аутрича",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Название компании",
                        },
                        "contact_name": {
                            "type": "string",
                            "description": "Имя контакта (если известно)",
                        },
                        "channel": {
                            "type": "string",
                            "enum": ["email", "telegram", "whatsapp", "linkedin"],
                            "description": "Канал отправки",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Тема письма (для email)",
                        },
                        "message_text": {
                            "type": "string",
                            "description": "Текст сообщения — готов к отправке",
                        },
                        "why_them": {
                            "type": "string",
                            "description": "Почему именно этот человек и эта компания — логика персонализации",
                        },
                    },
                    "required": [
                        "company_name",
                        "channel",
                        "message_text",
                        "why_them",
                    ],
                },
            },
            {
                "name": "set_session_summary",
                "description": "Итоговая сводка по сессии лидогенерации",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "total_leads": {
                            "type": "integer",
                            "description": "Всего лидов обработано",
                        },
                        "qualified": {
                            "type": "integer",
                            "description": "Прошли квалификацию (высокий + средний приоритет)",
                        },
                        "disqualified": {
                            "type": "integer",
                            "description": "Не прошли квалификацию",
                        },
                        "top_lead": {
                            "type": "string",
                            "description": "Самый перспективный лид этой сессии",
                        },
                        "estimated_pipeline": {
                            "type": "string",
                            "description": "Суммарный потенциал в рублях",
                        },
                        "recommended_action": {
                            "type": "string",
                            "description": "Что сделать прямо сейчас",
                        },
                    },
                    "required": [
                        "total_leads",
                        "qualified",
                        "disqualified",
                        "recommended_action",
                    ],
                },
            },
        ]

    def run(self, context: dict) -> dict:
        """Квалифицировать лиды и подготовить персональный аутрич."""
        user_msg = self._build_user_message(context)
        messages = [{"role": "user", "content": user_msg}]
        _, tool_store = self._run_loop(messages)

        leads = tool_store.get("qualify_lead", [])
        outreach = tool_store.get("draft_outreach", [])
        summary = tool_store.get("set_session_summary", [{}])[0]

        return {
            "leads": leads,
            "outreach": outreach,
            "summary": summary,
            "lead_count": len(leads),
            "qualified_count": sum(
                1 for l in leads if l.get("priority") in ["высокий", "средний"]
            ),
        }
