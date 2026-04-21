#!/usr/bin/env python3
"""
CROID AI Agent Orchestration System
Entry point — interactive CLI.
"""
import json
import os
import sys
from pathlib import Path

import anthropic

import config
from orchestrator import Orchestrator
from utils.display import (
    console,
    print_banner,
    print_error,
    print_info,
    print_section,
    print_success,
)

# ── Example contexts for each workflow ───────────────────────────────────

EXAMPLE_CONTEXTS = {
    "new_lead": {
        "task": "Найти потенциальные заказы для компании CROID",
        "description": (
            "Ищем B2B-клиентов в сегментах: IT, ритейл, производство. "
            "Наши компетенции: разработка ПО на заказ, интеграции, автоматизация бизнес-процессов. "
            "Средний чек: 1-5 млн руб. Цикл сделки: 1-3 месяца. "
            "Целевые клиенты: средний бизнес 50-500 сотрудников, выручка от 500 млн руб."
        ),
        "current_pipeline": [
            "ООО 'АльфаТрейд' — ритейл, интерес к автоматизации склада, бюджет ~2 млн",
            "ГК 'Инноватик' — IT-компания, нужна интеграция с 1С и Bitrix24",
            "ПАО 'МегаПром' — производство, ищут систему управления производством (MES)",
        ],
        "geography": "Москва, Санкт-Петербург, регионы",
    },
    "process_app": {
        "task": "Обработать входящую заявку от клиента",
        "application_text": """
            Добрый день!

            Мы компания ООО 'ТехноГрупп', занимаемся оптовой торговлей электроникой.
            Нам нужна система управления складом (WMS) с интеграцией в нашу 1С:Предприятие 8.3.

            Требования:
            - Учёт поступления и отгрузки товаров
            - Адресное хранение (3 склада, ~5000 ячеек)
            - Мобильные терминалы сбора данных (ТСД) — 10 устройств
            - Интеграция с 1С в режиме реального времени
            - Отчётность по остаткам, оборачиваемости, браку
            - Веб-интерфейс для руководителей

            Хотим запустить за 3 месяца. Бюджет — ориентировочно до 2,5 млн руб.
            Решение должно быть отечественным (реестр российского ПО желательно).

            Контакт: Петров Иван Сергеевич, директор по логистике, +7-999-123-45-67

            С уважением,
            Смирнов А.В., генеральный директор ТехноГрупп
        """,
        "company_info": "ООО 'ТехноГрупп', 250 сотрудников, выручка ~3 млрд руб./год",
    },
    "retain_clients": {
        "task": "Разработать стратегию возврата ушедших клиентов",
        "clients": [
            {
                "name": "ООО 'СтройМастер'",
                "segment": "строительство",
                "last_project": "Автоматизация документооборота, завершён 8 мес. назад",
                "revenue_history": "3 проекта за 2 года, суммарно 4,2 млн руб.",
                "last_contact": "6 месяцев назад, не ответили на письмо",
                "known_issues": "Были недовольны сроками сдачи последнего этапа",
            },
            {
                "name": "АО 'ФинТехРешения'",
                "segment": "финтех",
                "last_project": "Разработка API для банкинга, завершён 4 мес. назад",
                "revenue_history": "1 крупный проект на 7,5 млн руб.",
                "last_contact": "2 месяца назад, просили КП на новый проект, не отправили вовремя",
                "known_issues": "Запрашивали расширение команды, не смогли обеспечить",
            },
            {
                "name": "ИП Козлов Д.В.",
                "segment": "малый бизнес",
                "last_project": "Сайт + CRM-интеграция, 6 мес. назад",
                "revenue_history": "2 небольших проекта, ~800 тыс. руб.",
                "last_contact": "3 месяца назад",
                "known_issues": "Ценовой вопрос — нашёл дешевле",
            },
        ],
    },
    "revenue_audit": {
        "task": "Аудит выручки и рекомендации по росту",
        "current_state": {
            "monthly_revenue": "2,8 млн руб. в среднем за последние 3 месяца",
            "revenue_by_service": {
                "Разработка ПО на заказ": "55%",
                "Поддержка и обслуживание": "20%",
                "Консалтинг и аналитика": "15%",
                "Обучение": "10%",
            },
            "active_clients": 12,
            "pipeline_value": "8,5 млн руб. (сделки в работе)",
            "avg_check": "1,1 млн руб.",
            "sales_cycle": "45 дней в среднем",
            "conversion_rate": "28% от лида до сделки",
        },
        "challenges": [
            "Длинный цикл сделки — теряем горячих клиентов",
            "Низкая повторная покупка — клиенты не возвращаются",
            "Нет пакетных предложений",
            "Поддержка приносит мало денег но занимает ресурсы",
        ],
        "target": "Выйти на 5 млн руб./месяц за 6 месяцев",
    },
    "full_pipeline": {
        "task": "Полный коммерческий анализ и подготовка к сделке",
        "business_context": (
            "Компания CROID — разработка ПО на заказ. "
            "Специализация: ERP/WMS системы, мобильные приложения, интеграции. "
            "Целевой рынок: средний и крупный бизнес в России."
        ),
        "market_focus": "Ритейл и e-commerce, логистика, производство",
        "company_size": "20 разработчиков, 3 PM, 2 аналитика",
        "financial_goal": "Привлечь 2-3 новых клиента с суммарным чеком 8+ млн руб.",
    },
}


# ── CLI helpers ───────────────────────────────────────────────────────────


def prompt(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{question}{suffix}: ").strip()
        return answer or default
    except (EOFError, KeyboardInterrupt):
        return default


def select_workflow() -> str:
    """Interactive workflow selector."""
    workflows = list(Orchestrator.WORKFLOWS.items())
    console.print("\n[bold]Выберите workflow:[/bold]")
    for i, (key, desc) in enumerate(workflows, 1):
        console.print(f"  [cyan]{i}[/cyan]. {desc}")

    while True:
        choice = prompt("\nВведите номер (1–5)", "1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(workflows):
                return workflows[idx][0]
        except ValueError:
            pass
        console.print("[red]Введите число от 1 до 5[/red]")


def load_context(workflow: str) -> dict:
    """Load context: use example or accept custom JSON."""
    example = EXAMPLE_CONTEXTS.get(workflow, {})

    console.print("\n[bold]Контекст для агентов:[/bold]")
    console.print("  [cyan]1[/cyan]. Использовать пример (рекомендуется для демо)")
    console.print("  [cyan]2[/cyan]. Ввести свой JSON")
    console.print("  [cyan]3[/cyan]. Загрузить из файла")

    choice = prompt("Выбор", "1")

    if choice == "2":
        console.print("[dim]Введите JSON-контекст (одну строку или несколько, завершите пустой строкой):[/dim]")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        try:
            return json.loads("\n".join(lines))
        except json.JSONDecodeError as e:
            print_error(f"Ошибка парсинга JSON: {e}. Используем пример.")
            return example

    if choice == "3":
        path = prompt("Путь к JSON-файлу")
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print_error(f"Не удалось загрузить файл: {e}. Используем пример.")
            return example

    return example


def save_report(report: str) -> None:
    """Optionally save the report to a file."""
    answer = prompt("\nСохранить отчёт в файл? (y/n)", "n")
    if answer.lower() != "y":
        return
    filename = prompt("Имя файла", "croid_report.md")
    try:
        Path(filename).write_text(report, encoding="utf-8")
        print_success(f"Отчёт сохранён: {filename}")
    except OSError as e:
        print_error(f"Не удалось сохранить: {e}")


# ── Entry point ───────────────────────────────────────────────────────────


def main() -> None:
    print_banner(config.COMPANY_NAME)

    # Quick API key check
    if not os.getenv("ANTHROPIC_API_KEY"):
        print_error("ANTHROPIC_API_KEY не задан!")
        console.print("[dim]Создайте файл .env из .env.example и задайте API-ключ.[/dim]")
        sys.exit(1)

    # Check if single-run CLI args provided
    if len(sys.argv) > 1:
        # Support: python main.py <workflow> [context.json]
        workflow_arg = sys.argv[1]
        if workflow_arg not in Orchestrator.WORKFLOWS:
            print_error(f"Неизвестный workflow: {workflow_arg}")
            console.print(f"Доступные: {', '.join(Orchestrator.WORKFLOWS)}")
            sys.exit(1)
        context = {}
        if len(sys.argv) > 2:
            try:
                with open(sys.argv[2], encoding="utf-8") as f:
                    context = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print_error(f"Ошибка загрузки контекста: {e}")
                sys.exit(1)
        else:
            context = EXAMPLE_CONTEXTS.get(workflow_arg, {})
    else:
        # Interactive mode
        workflow_arg = select_workflow()
        context = load_context(workflow_arg)

    # Show selected workflow
    desc = Orchestrator.WORKFLOWS[workflow_arg]
    print_section("Запуск", f"**Workflow**: {desc}\n**Модель**: {config.MODEL}")

    # Run
    try:
        orch = Orchestrator()
    except RuntimeError as e:
        print_error(str(e))
        sys.exit(1)

    workflow_result = orch.run(workflow_arg, context)

    if workflow_result.errors:
        for err in workflow_result.errors:
            print_error(err)
    else:
        print_success(f"Workflow завершён. Выполнено шагов: {len(workflow_result.steps)}")

    # Generate and display report
    report = orch.format_report(workflow_result)
    print_section("Итоговый отчёт", report[:3000] + ("..." if len(report) > 3000 else ""))
    save_report(report)


if __name__ == "__main__":
    main()
