"""AmoCRM API client с поддержкой долгосрочных токенов и OAuth2."""
import json
import time
from pathlib import Path
from typing import Optional

import requests


TOKEN_FILE = Path(__file__).parent.parent / ".amocrm_tokens.json"


class AmoCRMClient:
    """
    Клиент для работы с AmoCRM API v4.

    Режим 1 — долгосрочный токен (рекомендуется, фича с фев 2024):
        client = AmoCRMClient("croid", long_term_token="ваш_токен")
        client.create_lead(...)  # работает сразу

    Режим 2 — OAuth2 (если нужен полный flow):
        client = AmoCRMClient("croid", client_id=..., client_secret=...)
        client.authorize(authorization_code)  # один раз
        client.create_lead(...)               # дальше работает сам
    """

    def __init__(
        self,
        subdomain: str,
        long_term_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: str = "https://localhost",
    ):
        self.subdomain = subdomain
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._access_token: Optional[str] = long_term_token
        self._refresh_token: Optional[str] = None
        # Долгосрочный токен не истекает в рамках сессии — ставим далёкое будущее
        self._token_expires_at: float = float("inf") if long_term_token else 0
        self._long_term_mode: bool = long_term_token is not None
        if not self._long_term_mode:
            self._load_tokens()

    # ── Авторизация ───────────────────────────────────────────────────────

    def get_auth_url(self) -> str:
        """Ссылка для получения authorization code (открыть в браузере один раз)."""
        return (
            f"https://www.amocrm.ru/oauth?"
            f"client_id={self.client_id}"
            f"&state=croid_bot"
            f"&mode=post_message"
        )

    def authorize(self, code: str) -> None:
        """Обменять authorization code на access + refresh токены."""
        resp = requests.post(
            f"https://{self.subdomain}.amocrm.ru/oauth2/access_token",
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
            },
        )
        resp.raise_for_status()
        self._save_tokens(resp.json())

    def _refresh(self) -> None:
        """Обновить access token через refresh token."""
        resp = requests.post(
            f"https://{self.subdomain}.amocrm.ru/oauth2/access_token",
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "redirect_uri": self.redirect_uri,
            },
        )
        resp.raise_for_status()
        self._save_tokens(resp.json())

    def _save_tokens(self, data: dict) -> None:
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 86400) - 60
        TOKEN_FILE.write_text(json.dumps({
            "access_token": self._access_token,
            "refresh_token": self._refresh_token,
            "expires_at": self._token_expires_at,
        }))

    def _load_tokens(self) -> None:
        if TOKEN_FILE.exists():
            data = json.loads(TOKEN_FILE.read_text())
            self._access_token = data.get("access_token")
            self._refresh_token = data.get("refresh_token")
            self._token_expires_at = data.get("expires_at", 0)

    def _headers(self) -> dict:
        if not self._long_term_mode and time.time() >= self._token_expires_at:
            self._refresh()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"https://{self.subdomain}.amocrm.ru/api/v4{path}"

    def _post(self, path: str, data: dict) -> dict:
        resp = requests.post(self._url(path), json=data, headers=self._headers())
        resp.raise_for_status()
        return resp.json() if resp.text else {}

    def _get(self, path: str, params: dict = None) -> dict:
        resp = requests.get(self._url(path), params=params, headers=self._headers())
        resp.raise_for_status()
        return resp.json() if resp.text else {}

    # ── Утилиты ───────────────────────────────────────────────────────────

    def check_connection(self) -> dict:
        """Проверить соединение и вернуть данные аккаунта."""
        return self._get("/account")

    # ── Контакты ──────────────────────────────────────────────────────────

    def create_contact(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
    ) -> int:
        """Создать контакт, вернуть его id."""
        custom_fields = []
        if email:
            custom_fields.append({"field_code": "EMAIL", "values": [{"value": email, "enum_code": "WORK"}]})
        if phone:
            custom_fields.append({"field_code": "PHONE", "values": [{"value": phone, "enum_code": "WORK"}]})

        payload = [{"name": name, "custom_fields_values": custom_fields}]
        if company:
            payload[0]["company_name"] = company

        result = self._post("/contacts", payload)
        return result["_embedded"]["contacts"][0]["id"]

    # ── Сделки ────────────────────────────────────────────────────────────

    def create_lead(
        self,
        name: str,
        contact_id: Optional[int] = None,
        pipeline_id: Optional[int] = None,
        status_id: Optional[int] = None,
        price: Optional[int] = None,
        tags: Optional[list[str]] = None,
    ) -> int:
        """Создать сделку, вернуть её id."""
        payload: dict = {"name": name}
        if price:
            payload["price"] = price
        if pipeline_id:
            payload["pipeline_id"] = pipeline_id
        if status_id:
            payload["status_id"] = status_id
        if tags:
            payload["_embedded"] = {"tags": [{"name": t} for t in tags]}
        if contact_id:
            payload.setdefault("_embedded", {})["contacts"] = [{"id": contact_id}]

        result = self._post("/leads", [payload])
        return result["_embedded"]["leads"][0]["id"]

    # ── Примечания ────────────────────────────────────────────────────────

    def add_note_to_lead(self, lead_id: int, text: str, note_type: str = "common") -> None:
        """Добавить заметку к сделке."""
        self._post(f"/leads/{lead_id}/notes", [{
            "note_type": note_type,
            "params": {"text": text},
        }])

    # ── Задачи ────────────────────────────────────────────────────────────

    def create_task(
        self,
        lead_id: int,
        text: str,
        due_hours: int = 24,
        task_type_id: int = 1,
    ) -> None:
        """Создать задачу привязанную к сделке."""
        self._post("/tasks", [{
            "task_type_id": task_type_id,
            "text": text,
            "complete_till": int(time.time()) + due_hours * 3600,
            "entity_id": lead_id,
            "entity_type": "leads",
        }])

    # ── Высокоуровневый метод для лидогенератора ──────────────────────────

    def push_lead_from_agent(
        self,
        company_name: str,
        contact_name: Optional[str],
        contact_email: Optional[str],
        trigger: str,
        icp_score: int,
        priority: str,
        estimated_order: Optional[str],
        source: str,
        draft_message: Optional[str],
        pipeline_id: Optional[int] = None,
    ) -> int:
        """
        Создать контакт + сделку + заметки + задачу одним вызовом.
        Возвращает id созданной сделки.
        """
        contact_id = None
        if contact_name or contact_email:
            contact_id = self.create_contact(
                name=contact_name or company_name,
                email=contact_email,
                company=company_name,
            )

        lead_name = f"{company_name} | {source} | ICP {icp_score}/10"
        price = None
        if estimated_order:
            digits = "".join(c for c in estimated_order if c.isdigit())
            if digits:
                price = int(digits[:7])

        lead_id = self.create_lead(
            name=lead_name,
            contact_id=contact_id,
            pipeline_id=pipeline_id,
            price=price,
            tags=[source, priority, f"icp-{icp_score}"],
        )

        self.add_note_to_lead(lead_id, f"Триггер: {trigger}")

        if draft_message:
            self.add_note_to_lead(lead_id, f"Черновик письма:\n\n{draft_message}")

        self.create_task(
            lead_id=lead_id,
            text=f"Проверить черновик и отправить письмо — {company_name}",
            due_hours=4,
        )

        return lead_id
