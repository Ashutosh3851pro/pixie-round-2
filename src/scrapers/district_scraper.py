import re
from datetime import datetime
from typing import List, Optional
import json

from src.scrapers.base_scraper import BaseScraper
from src.models.event import Event


class DistrictScraper(BaseScraper):
    def get_platform_name(self) -> str:
        return "District"

    def get_base_url(self) -> str:
        urls = self.config.get_city_url_mapping("district")
        return urls.get(self.city, "")

    def parse_events(self, html_content: str) -> List[Event]:
        events = []
        soup = self.get_soup(html_content)
        link_hints = self._extract_event_links(soup)

        if not link_hints:
            self.logger.warning("No event links found")
            return []

        for link, venue_hint in list(link_hints.items())[:25]:
            try:
                event_html = self.fetch_page(link)
                if not event_html:
                    continue
                event = self._parse_event_page(event_html, link, venue_hint)
                if event and self.validate_event(event):
                    events.append(event)
            except Exception as e:
                self.logger.debug(f"Skip event: {e}")
                continue

        return events

    def _is_valid_event_url(self, url: str) -> bool:
        url = url.split("?")[0].rstrip("/")
        if url.endswith("/events") or url.endswith("/event"):
            return False
        for prefix in ["/events/", "/event/"]:
            if prefix in url:
                rest = url.split(prefix, 1)[1]
                return bool(rest and not rest.startswith("/"))
        return False

    def _extract_venue_city_from_text(self, text: str) -> Optional[str]:
        match = re.search(r"([A-Za-z0-9\s&|]+,\s*[A-Za-z0-9/]+)(?:\s*₹|\s*Free|$)", text)
        if match:
            return self._parse_city_from_venue(match.group(1))
        return None

    def _extract_event_links(self, soup) -> dict:
        result = {}
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/artist" in href:
                continue
            if "/events/" in href or "/event/" in href:
                if href.startswith("/"):
                    href = f"https://www.district.in{href}"
                if href.startswith("http") and self._is_valid_event_url(href):
                    url = href.split("?")[0]
                    text = a.get_text(separator=" ", strip=True)
                    hint = self._extract_venue_city_from_text(text) or self._parse_city_from_venue(text)
                    result[url] = hint
        return result

    def _parse_city_from_venue(self, venue: str) -> Optional[str]:
        if not venue or "," not in venue:
            return None
        parts = [p.strip() for p in venue.split(",") if p.strip()]
        if not parts:
            return None
        skip = {"india", "in"}
        for p in reversed(parts):
            if p.lower() in skip or p.isdigit() or len(p) > 50:
                continue
            return p
        return parts[-1] if parts else None

    def _parse_event_page(self, html_content: str, url: str, venue_hint: Optional[str] = None) -> Optional[Event]:
        try:
            soup = self.get_soup(html_content)
            event_name = "Unknown Event"
            event_date = "TBA"
            venue = "TBA"
            city = venue_hint if venue_hint else self.city
            category = "General"

            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "{}")
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if isinstance(item, dict) and item.get("@type") == "Event":
                            event_name = item.get("name", event_name)
                            event_date = item.get("startDate", event_date)
                            category = (
                                item.get("eventType") or item.get("genre") or category
                            )
                            loc = item.get("location", {})
                            if isinstance(loc, dict):
                                venue = loc.get("name") or venue
                                addr = loc.get("address", {})
                                if isinstance(addr, dict):
                                    locality = addr.get("addressLocality")
                                    if locality:
                                        city = locality
                                if city == self.city and venue != "TBA" and "," in venue:
                                    parsed = self._parse_city_from_venue(venue)
                                    if parsed:
                                        city = parsed
                            break
                except Exception:
                    continue

            if event_name == "Unknown Event":
                h1 = soup.find("h1")
                event_name = h1.get_text(strip=True) if h1 else event_name
            if event_date == "TBA":
                meta = soup.find("meta", property="event:start_date")
                if meta and meta.get("content"):
                    event_date = meta["content"]
            if venue == "TBA":
                meta = soup.find("meta", property="event:location")
                if meta and meta.get("content"):
                    venue = meta["content"]

            if city == self.city and venue != "TBA" and "," in venue:
                parsed = self._parse_city_from_venue(venue)
                if parsed:
                    city = parsed

            if city == self.city:
                for elem in soup.find_all(["p", "div", "span"]):
                    text = elem.get_text(strip=True)
                    if "," in text and 8 < len(text) < 70:
                        parsed = self._parse_city_from_venue(text)
                        if parsed and parsed.lower() not in ("india", "tba", "free"):
                            city = parsed
                            break

            return Event(
                event_name=event_name,
                date=event_date,
                venue=venue,
                city=city,
                category=category,
                url=url,
                source=self.get_platform_name(),
                status="Active",
                last_updated=datetime.now(),
            )
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
