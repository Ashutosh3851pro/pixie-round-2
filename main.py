from typing import List
from pathlib import Path

from src.utils.config import config
from src.scrapers.district_scraper import DistrictScraper
from src.storage.google_sheets_storage import GoogleSheetsStorage


def get_scrapers(city: str, platforms: List[str]):
    mapping = {"district": DistrictScraper}
    return [
        mapping[p.strip().lower()](city)
        for p in platforms
        if mapping.get(p.strip().lower())
    ]


def run_once(city: str, platforms: List[str] | None = None) -> int:
    if not config.GOOGLE_SHEETS_ID or not config.GOOGLE_CREDENTIALS_FILE:
        raise ValueError("Set GOOGLE_SHEETS_ID and GOOGLE_CREDENTIALS_FILE in .env")

    creds_path = Path(config.GOOGLE_CREDENTIALS_FILE)
    if not creds_path.is_absolute():
        creds_path = config.BASE_DIR / creds_path
    if not creds_path.exists():
        raise ValueError(f"Credentials file not found: {creds_path}")

    platforms = platforms or config.PLATFORMS
    events = []
    for scraper in get_scrapers(city, platforms):
        events.extend(scraper.scrape())

    if not events:
        return 0

    storage = GoogleSheetsStorage()
    storage.save_events(events)
    storage.mark_expired_events()
    return len(events)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--city", default=config.DEFAULT_CITY)
    p.add_argument("--platforms", default=",".join(config.PLATFORMS))
    args = p.parse_args()
    platforms = [x.strip() for x in args.platforms.split(",") if x.strip()]
    run_once(args.city, platforms)
