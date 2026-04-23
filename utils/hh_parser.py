"""Парсер hh.ru: ищет компании с ICP-вакансиями для лидогенерации."""
import time
from typing import Optional

import requests

HH_API = "https://api.hh.ru"
HEADERS = {"User-Agent": "CROID-LeadBot/1.0"}

# Ключевые запросы — роли, которые указывают на потребность в мерче
ICP_QUERIES = [
    "руководитель корпоративной культуры",
    "руководитель внутренних коммуникаций",
    "HR директор",
    "People директор",
    "event менеджер корпоративный",
    "офис менеджер",
]

# Агентства — фильтруем по названию отрасли или имени работодателя
AGENCY_INDUSTRY_KEYWORDS = [
    "кадров", "рекрутинг", "подбор персонала", "staffing",
    "headhunting", "аутсорсинг персонала",
]
AGENCY_NAME_KEYWORDS = [
    "агентство", "рекрутинг", "кадровое", "staffing",
    "headhunting", "recruitment", "hr-консалт",
]

# Москва = 1, Санкт-Петербург = 2
DEFAULT_AREAS = [1, 2]


def _get(path: str, params: dict = None) -> dict:
    resp = requests.get(f"{HH_API}{path}", params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _is_agency(employer_name: str, industries: list[dict]) -> bool:
    name_lower = employer_name.lower()
    if any(kw in name_lower for kw in AGENCY_NAME_KEYWORDS):
        return True
    for ind in industries:
        ind_lower = ind.get("name", "").lower()
        if any(kw in ind_lower for kw in AGENCY_INDUSTRY_KEYWORDS):
            return True
    return False


def _get_employer_details(employer_id: int) -> dict:
    try:
        return _get(f"/employers/{employer_id}")
    except Exception:
        return {}


def _extract_company_size(employer: dict) -> Optional[str]:
    """Возвращает диапазон сотрудников из профиля работодателя."""
    size = employer.get("size")
    if size:
        return size.get("name")
    return None


def fetch_leads(
    queries: list[str] = None,
    areas: list[int] = None,
    pages_per_query: int = 2,
    per_page: int = 20,
) -> list[dict]:
    """
    Ищет компании на hh.ru по ICP-запросам.
    Возвращает список уникальных компаний, отфильтровав агентства.
    """
    queries = queries or ICP_QUERIES
    areas = areas or DEFAULT_AREAS

    seen_employer_ids: set[int] = set()
    leads: list[dict] = []

    for query in queries:
        for area in areas:
            for page in range(pages_per_query):
                try:
                    data = _get("/vacancies", params={
                        "text": query,
                        "area": area,
                        "per_page": per_page,
                        "page": page,
                        "search_field": "name",  # ищем только в названии вакансии
                    })
                except Exception as e:
                    print(f"  hh.ru: ошибка запроса ({query}, area={area}, page={page}): {e}")
                    continue

                for vacancy in data.get("items", []):
                    employer = vacancy.get("employer", {})
                    employer_id = employer.get("id")
                    if not employer_id or employer_id in seen_employer_ids:
                        continue
                    seen_employer_ids.add(employer_id)

                    employer_name = employer.get("name", "")

                    # Быстрая проверка по имени до запроса деталей
                    if any(kw in employer_name.lower() for kw in AGENCY_NAME_KEYWORDS):
                        continue

                    # Детали работодателя (отрасли, размер, сайт)
                    details = _get_employer_details(employer_id)
                    industries = details.get("industries", [])

                    if _is_agency(employer_name, industries):
                        continue

                    company_size = _extract_company_size(details)
                    area_name = vacancy.get("area", {}).get("name", "")
                    industry_names = [i.get("name") for i in industries if i.get("name")]

                    leads.append({
                        "company_name": employer_name,
                        "hh_employer_id": employer_id,
                        "vacancy_title": vacancy.get("name"),
                        "vacancy_url": vacancy.get("alternate_url"),
                        "employer_url": details.get("alternate_url"),
                        "site_url": details.get("site_url"),
                        "city": area_name,
                        "company_size": company_size,
                        "industries": industry_names,
                        "trigger": f"Нанимают «{vacancy.get('name')}» — {area_name}",
                        "source": "hh.ru",
                    })

                    time.sleep(0.25)  # вежливая пауза между запросами к API

    return leads


def fetch_leads_summary(leads: list[dict]) -> str:
    """Текстовое резюме для передачи агенту-лидогенератору."""
    lines = [f"Найдено {len(leads)} компаний на hh.ru:\n"]
    for i, lead in enumerate(leads, 1):
        industries = ", ".join(lead["industries"][:2]) if lead["industries"] else "—"
        lines.append(
            f"{i}. {lead['company_name']} | {lead['city']} | "
            f"{lead.get('company_size') or 'размер неизвестен'} | "
            f"{industries}\n"
            f"   Вакансия: {lead['vacancy_title']}\n"
            f"   Триггер: {lead['trigger']}\n"
        )
    return "\n".join(lines)
