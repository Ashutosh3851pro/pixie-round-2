from abc import ABC, abstractmethod
from typing import List, Optional
import time

from bs4 import BeautifulSoup

from src.models.event import Event
from src.utils.config import config
from src.utils.logger import setup_logger
from src.utils.helpers import retry_on_failure, make_request


logger = setup_logger(__name__)


class BaseScraper(ABC):
    def __init__(self, city: str):
        self.city = city
        self.config = config
        self.logger = logger
        self.events: List[Event] = []

    @abstractmethod
    def get_platform_name(self) -> str:
        pass

    @abstractmethod
    def get_base_url(self) -> str:
        pass

    @abstractmethod
    def parse_events(self, html_content: str) -> List[Event]:
        pass

    @retry_on_failure(max_retries=3, delay=2.0)
    def fetch_page(self, url: str) -> Optional[str]:
        try:
            self.logger.info(f"Fetching: {url}")
            response = make_request(url, timeout=self.config.REQUEST_TIMEOUT)
            time.sleep(self.config.RATE_LIMIT_DELAY)
            return response.text
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            raise

    def scrape(self) -> List[Event]:
        try:
            self.logger.info(f"Scraping {self.city} from {self.get_platform_name()}")
            url = self.get_base_url()
            if not url:
                self.logger.warning(f"No URL for {self.city}")
                return []

            html = self.fetch_page(url)
            if not html:
                return []

            self.events = self.parse_events(html)
            self.logger.info(f"Found {len(self.events)} events")
            return self.events
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return []

    def get_soup(self, html_content: str) -> BeautifulSoup:
        return BeautifulSoup(html_content, "html.parser")

    def validate_event(self, event: Event) -> bool:
        for field in ["event_name", "date", "venue", "city", "url"]:
            if not getattr(event, field, None):
                self.logger.warning(f"Event missing {field}")
                return False
        return True
