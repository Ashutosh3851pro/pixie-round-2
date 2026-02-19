# Event Scraper & Analytics Platform

A full-stack system that scrapes **EVENTS** (not movies) from District.in, stores and deduplicates the data in Google Sheets, and displays analytics on a live dashboard.

## How to Run

```bash
python run.py
```

Scrapes events, then starts the dashboard at http://localhost:8000

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  District.in    │────▶│  Scraper         │────▶│  Google Sheets  │
│  /events/       │     │  main.py         │     │  (Events sheet) │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                       │
                                 └───────────────────────┘
                                            │
                                            ▼
                                 ┌─────────────────┐
                                 │  FastAPI +      │
                                 │  Dashboard     │
                                 └─────────────────┘
```

- **Scraper**: Fetches https://www.district.in/events/, extracts event links, visits each event page, parses JSON-LD and HTML
- **Storage**: Google Sheets only (no database). Requires `GOOGLE_SHEETS_ID` and `credentials.json`
- **API**: FastAPI serves `/api/events`, `/api/analytics`, and the dashboard UI

## Scraping Strategy

1. **Target**: https://www.district.in/events/ (live events – concerts, comedy, workshops, etc.)
2. **Flow**: Fetch events listing → extract event links → visit each event page
3. **URL filter**: Only links with a path after `/events/` (e.g. `/events/event-name`) – skips the listing page itself
4. **Parsing**: JSON-LD `@type: Event` first; fallback to meta tags and HTML
5. **City extraction**: From listing page cards, JSON-LD `addressLocality`, or venue string (e.g. "Gymkhana Club, Gurugram")
6. **Rate limiting**: Configurable delay between requests

## Deduplication

- **Event ID**: MD5 hash of `event_name + date + venue + city` (first 12 chars)
- **Merge**: On save, new events are merged with existing by `event_id`; existing events get `last_updated` refreshed
- **Status**: Only `Active` or `Expired` (no "Updated" tag)

## Expiry

Events past `MARK_EXPIRED_DAYS` (default 0) are marked `Expired` on each scrape.

## Environment Variables

Create `.env` from `.env.example`. **Required:**

| Variable | Description |
|----------|-------------|
| `GOOGLE_SHEETS_ID` | Sheet ID from the Google Sheet URL |
| `GOOGLE_CREDENTIALS_FILE` | Path to service account JSON (default: credentials.json) |

**Optional:**

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_CITY` | Mumbai | City used when scraping (city is also extracted per event) |
| `PLATFORMS` | district | Comma-separated platforms |
| `MARK_EXPIRED_DAYS` | 0 | Days offset for marking events expired |
| `RATE_LIMIT_DELAY` | 2 | Seconds between requests |

## Google Sheets Setup

1. Create a [Google Cloud project](https://console.cloud.google.com/), enable Sheets API
2. Create a service account, download JSON key
3. Save as `credentials.json` in project root
4. Create a Google Sheet, share it with the service account email (Editor)
5. Set `GOOGLE_SHEETS_ID` to the sheet ID from the URL
6. The scraper writes to the "Events" worksheet (or first sheet)

## Quick Start

```bash
git clone https://github.com/Ashutosh3851pro/pixie-round-2.git
cd pixie-round-2
python -m venv .venv
source .venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env – set GOOGLE_SHEETS_ID and add credentials.json
python run.py
```

Open http://localhost:8000 for the dashboard.

## Scheduling

Run the scraper periodically via cron:

```bash
0 */6 * * * cd /path/to/project && /path/to/venv/bin/python main.py
```

## Project Structure

```
├── api/
│   └── main.py              # FastAPI app + dashboard
├── frontend/
│   └── index.html           # Dashboard UI
├── src/
│   ├── scrapers/            # base_scraper, district_scraper
│   ├── storage/             # base_storage, google_sheets_storage
│   ├── models/              # Event model
│   └── utils/               # config, helpers, logger
├── main.py                  # Scraper (used by run.py and cron)
├── run.py                   # Scrape + serve
└── requirements.txt
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/api/events` | GET | List events (query: city, status, source, limit, offset) |
| `/api/analytics` | GET | Stats (total, active, expired, by city, by source, by category) |
