from abc import ABC, abstractmethod
from typing import List

from src.models.event import Event


class BaseStorage(ABC):
    def merge_events(
        self, new_events: List[Event], existing_events: List[Event]
    ) -> List[Event]:
        event_dict = {e.event_id: e for e in existing_events}
        for event in new_events:
            if event.event_id in event_dict:
                event_dict[event.event_id].last_updated = event.last_updated
            else:
                event_dict[event.event_id] = event
        return list(event_dict.values())

    @abstractmethod
    def save_events(self, events: List[Event]) -> bool:
        pass

    @abstractmethod
    def load_events(self) -> List[Event]:
        pass

    @abstractmethod
    def mark_expired_events(self) -> int:
        pass
