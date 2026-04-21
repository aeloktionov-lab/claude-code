# CROID AI — Оркестратор агентов

Система из 6 ИИ-агентов, которые помогают компании CROID искать заказы, обрабатывать заявки, считать стоимость, готовить коммерческие предложения, возвращать клиентов и оптимизировать выручку.

---

## Что нужно для запуска

- Компьютер с macOS или Windows
- Интернет
- API-ключ Anthropic (получить на [console.anthropic.com](https://console.anthropic.com))

---

## Установка — один раз

### Шаг 1. Установить Python

**macOS:**
1. Откройте Terminal (Finder → Программы → Утилиты → Terminal)
2. Введите команду и нажмите Enter:
   ```
   python3 --version
   ```
3. Если видите `Python 3.10` или выше — Python уже установлен, переходите к Шагу 2
4. Если нет — скачайте с [python.org/downloads](https://www.python.org/downloads/) и установите

**Windows:**
1. Откройте командную строку (Win+R → напишите `cmd` → Enter)
2. Введите:
   ```
   python --version
   ```
3. Если не установлен — скачайте с [python.org/downloads](https://www.python.org/downloads/), при установке обязательно поставьте галочку **"Add Python to PATH"**

---

### Шаг 2. Скачать проект

Если у вас установлен Git:
```
git clone https://github.com/aeloktionov-lab/claude-code.git
cd claude-code
```

Или просто скачайте ZIP с GitHub и распакуйте в удобную папку.

---

### Шаг 3. Установить зависимости

В Terminal (macOS) или командной строке (Windows) перейдите в папку проекта и выполните:

```
pip install -r requirements.txt
```

Это установит все необходимые библиотеки. Занимает 1–2 минуты.

---

### Шаг 4. Создать файл с API-ключом

1. В папке проекта найдите файл `.env.example`
2. Скопируйте его и назовите копию `.env` (без слова "example")
3. Откройте файл `.env` любым текстовым редактором (Блокнот, TextEdit)
4. Замените `your_api_key_here` на ваш реальный ключ Anthropic:

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
COMPANY_NAME=CROID
ANTHROPIC_MODEL=claude-sonnet-4-6
```

5. Сохраните файл

> Где взять ключ: зайдите на [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key

---

## Запуск

### Интерактивный режим (рекомендуется)

```
python main.py
```

После запуска система спросит:
1. **Какой workflow выбрать** — введите цифру от 1 до 5
2. **Какой контекст использовать** — нажмите Enter, чтобы использовать готовый пример

### Режим командной строки (для автоматизации)

```
python main.py <workflow>
python main.py <workflow> context.json
```

Примеры:
```
python main.py new_lead
python main.py process_app my_application.json
```

---

## Что делает каждый workflow

| # | Название | Команда | Что происходит |
|---|----------|---------|----------------|
| 1 | Полный pipeline | `full_pipeline` | Поиск лидов → обработка заявки → расчёт стоимости → КП → анализ выручки |
| 2 | Поиск лидов | `new_lead` | Находит и квалифицирует потенциальных B2B-клиентов |
| 3 | Обработка заявки | `process_app` | Разбирает входящую заявку → считает стоимость → готовит КП |
| 4 | Возврат клиентов | `retain_clients` | Анализирует ушедших клиентов, пишет письма для реактивации |
| 5 | Аудит выручки | `revenue_audit` | Находит узкие места и даёт рекомендации по росту выручки |

---

## Как передать свои данные

По умолчанию система использует демо-данные. Чтобы передать реальные данные, создайте JSON-файл.

### Пример для обработки заявки (`process_app`)

Создайте файл `my_app.json`:
```json
{
  "task": "Обработать входящую заявку",
  "application_text": "Здесь вставьте текст заявки от клиента...",
  "company_info": "Название компании, размер, отрасль"
}
```

Запустите:
```
python main.py process_app my_app.json
```

### Пример для поиска лидов (`new_lead`)

Создайте файл `search.json`:
```json
{
  "task": "Найти потенциальные заказы",
  "description": "Описание того, что ищем и для кого",
  "geography": "Москва, Санкт-Петербург"
}
```

---

## Сохранение отчёта

После завершения работы система спросит: **«Сохранить отчёт в файл? (y/n)»**

- Нажмите `y` и Enter → введите имя файла (или нажмите Enter для имени по умолчанию)
- Нажмите `n` и Enter → отчёт не сохраняется

Отчёт сохраняется в формате Markdown (`.md`), который можно открыть в любом текстовом редакторе или в Notion.

---

## Частые проблемы

**«ANTHROPIC_API_KEY не задан»**
→ Проверьте, что файл `.env` создан и ключ вписан без лишних пробелов

**«No module named 'anthropic'»**
→ Выполните `pip install -r requirements.txt` ещё раз

**«python: command not found»** (macOS/Linux)
→ Используйте `python3` вместо `python`

**Ошибка при запуске на Windows**
→ Откройте PowerShell от имени администратора и выполните:
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Структура проекта

```
claude-code/
├── main.py              — точка входа, CLI
├── orchestrator.py      — связывает агентов в workflow
├── config.py            — настройки (модель, токены)
├── .env                 — ваш API-ключ (создаётся вручную)
├── .env.example         — шаблон для .env
├── requirements.txt     — зависимости Python
├── agents/
│   ├── base.py          — базовый класс всех агентов
│   ├── order_search.py         — агент поиска заказов
│   ├── application_processor.py — агент обработки заявок
│   ├── cost_optimizer.py       — агент расчёта стоимости
│   ├── proposal_generator.py   — агент подготовки КП
│   ├── client_retention.py     — агент возврата клиентов
│   └── revenue_optimizer.py    — агент оптимизации выручки
└── utils/
    └── display.py       — красивый вывод в консоль
```
