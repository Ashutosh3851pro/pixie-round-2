from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib


@dataclass
class Event:
    event_name: str
    date: str
    venue: str
    city: str
    category: str
    url: str
    source: str
    status: str = "Active"
    last_updated: datetime = field(default_factory=datetime.now)
    event_id: Optional[str] = None

    def __post_init__(self):
        if not self.event_id:
            self.event_id = self._generate_id()

    def _generate_id(self) -> str:
        text = f"{self.event_name}_{self.date}_{self.venue}_{self.city}"
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        return {
            "Event ID": self.event_id,
            "Event Name": self.event_name,
            "Date": self.date,
            "Venue": self.venue,
            "City": self.city,
            "Category": self.category,
            "URL": self.url,
            "Source": self.source,
            "Status": self.status,
            "Last Updated": self.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
        }
