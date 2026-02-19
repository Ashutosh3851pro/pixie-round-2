import json
from pathlib import Path
from typing import List
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from src.storage.base_storage import BaseStorage
from src.models.event import Event
from src.utils.config import config
from src.utils.helpers import is_date_expired, parse_date

HEADERS = [
    "Event ID",
    "Event Name",
    "Date",
    "Venue",
    "City",
    "Category",
    "URL",
    "Source",
    "Status",
    "Last Updated",
]


class GoogleSheetsStorage(BaseStorage):
    def __init__(
        self,
        sheet_id: str = None,
        credentials_file: str = None,
        credentials_json: str = None,
    ):
        super().__init__()
        self.sheet_id = sheet_id or config.GOOGLE_SHEETS_ID
        self.credentials_json = credentials_json or config.GOOGLE_CREDENTIALS
        self._client = None
        self._worksheet = None

    def _get_client(self):
        has_creds = bool(self.credentials_json)
        if not has_creds or not self.sheet_id:
            raise ValueError(
                "Set GOOGLE_SHEETS_ID and either GOOGLE_CREDENTIALS (JSON string) "
                "or GOOGLE_CREDENTIALS_FILE"
            )
        if self._client is None:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            if self.credentials_json:
                info = json.loads(self.credentials_json)
                creds = Credentials.from_service_account_info(info, scopes=scopes)
            self._client = gspread.authorize(creds)
        return self._client

    def _get_worksheet(self):
        if self._worksheet is None:
            sheet = self._get_client().open_by_key(self.sheet_id)
            try:
                self._worksheet = sheet.worksheet("Events")
            except Exception:
                self._worksheet = sheet.sheet1
        return self._worksheet

    def save_events(self, events: List[Event]) -> bool:
        try:
            ws = self._get_worksheet()
            existing = self.load_events()
            merged = self.merge_events(events, existing)
            for e in merged:
                if e.status == "Updated":
                    e.status = "Active"
            rows = [
                [
                    e.event_id,
                    e.event_name,
                    e.date,
                    e.venue,
                    e.city,
                    e.category,
                    e.url,
                    e.source,
                    e.status,
                    e.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
                ]
                for e in merged
            ]
            ws.clear()
            ws.append_row(HEADERS)
            if rows:
                ws.update("A2", rows, value_input_option="RAW")
            return True
        except Exception:
            raise
            return False

    def load_events(self) -> List[Event]:
        try:
            ws = self._get_worksheet()
            records = ws.get_all_records()
            if not records:
                return []
            events = []
            for r in records:
                try:
                    lu = parse_date(str(r.get("Last Updated", ""))) or datetime.now()
                    status = str(r.get("Status", ""))
                    if status == "Updated":
                        status = "Active"
                    events.append(
                        Event(
                            event_name=str(r.get("Event Name", "")),
                            date=str(r.get("Date", "")),
                            venue=str(r.get("Venue", "")),
                            city=str(r.get("City", "")),
                            category=str(r.get("Category", "")),
                            url=str(r.get("URL", "")),
                            source=str(r.get("Source", "")),
                            status=status,
                            event_id=str(r.get("Event ID", "")),
                            last_updated=lu,
                        )
                    )
                except Exception:
                    continue
            return events
        except Exception:
            return []

    def mark_expired_events(self) -> int:
        try:
            events = self.load_events()
            count = 0
            for e in events:
                if e.status == "Active" and is_date_expired(
                    e.date, config.MARK_EXPIRED_DAYS
                ):
                    e.status = "Expired"
                    e.last_updated = datetime.now()
                    count += 1
            if count:
                self.save_events(events)
            return count
        except Exception:
            return 0

    def get_analytics(self) -> dict:
        events = self.load_events()
        active = [e for e in events if e.status == "Active"]
        by_city = {}
        for e in active:
            by_city[e.city] = by_city.get(e.city, 0) + 1
        by_source = {}
        for e in events:
            by_source[e.source] = by_source.get(e.source, 0) + 1
        by_category = {}
        for e in active:
            cat = e.category or "General"
            by_category[cat] = by_category.get(cat, 0) + 1
        return {
            "total_events": len(events),
            "active_events": len(active),
            "expired_events": len([e for e in events if e.status == "Expired"]),
            "by_city": by_city,
            "by_source": by_source,
            "by_category": by_category,
        }
