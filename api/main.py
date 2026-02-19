import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from src.storage.google_sheets_storage import GoogleSheetsStorage


app = FastAPI(title="Event Scraper API", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

storage = GoogleSheetsStorage()
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.get("/")
def serve_dashboard():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Event Scraper API. Use /api/events and /api/analytics"}


@app.get("/api/events")
def get_events(
    city: str = Query(None),
    status: str = Query(None),
    source: str = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    events = storage.load_events()
    if city:
        events = [e for e in events if e.city.lower() == city.lower()]
    if status:
        events = [e for e in events if e.status == status]
    if source:
        events = [e for e in events if e.source.lower() == source.lower()]
    total = len(events)
    events = events[offset : offset + limit]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "events": [e.to_dict() for e in events],
    }


@app.get("/api/analytics")
def get_analytics():
    return storage.get_analytics()
