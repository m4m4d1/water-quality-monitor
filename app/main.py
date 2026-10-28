"""REST API (and, once the web/ folder exists, the dashboard).

    uvicorn app.main:app --reload      # then open http://localhost:8000 and /docs

Environment variables:
    WQ_DB             SQLite file (default data/water.db)
    WQ_SIMULATE       1 (default) to add simulated readings every WQ_SIM_INTERVAL seconds
    WQ_SIM_INTERVAL   seconds between simulated readings (default 60)
    WQ_API_KEY        if set, POST /api/readings requires the header X-API-Key
"""
import asyncio
import os
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from . import __version__, db, quality, simulator
from .config import PARAMETERS, STATION_IDS, STATIONS, STATUS_BANDS
from .models import ReadingIn

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


async def simulate_forever(interval: int) -> None:
    rng = random.Random()
    while True:
        await asyncio.sleep(interval)
        now = datetime.now(timezone.utc)
        db.insert_readings([simulator.reading(s, now, rng) for s in STATIONS])


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    task = None
    if os.environ.get("WQ_SIMULATE", "1") == "1":
        if db.count() == 0:
            simulator.backfill(hours=72)
        task = asyncio.create_task(simulate_forever(int(os.environ.get("WQ_SIM_INTERVAL", "60"))))
    yield
    if task:
        task.cancel()


app = FastAPI(
    title="Water Quality Monitoring System",
    description="River water quality for Indonesia: readings, pollution index (Indeks Pencemaran) and alerts.",
    version=__version__,
    lifespan=lifespan,
)


def station_view(station: dict, latest: dict | None) -> dict:
    return {**station, "latest": quality.score(latest) if latest else None}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__, "readings": db.count()}


@app.get("/api/meta")
def meta() -> dict:
    """Parameters, limits and status bands, for building a UI."""
    return {"parameters": PARAMETERS, "status_bands": [
        {**b, "max": None if b["max"] == float("inf") else b["max"]} for b in STATUS_BANDS]}


@app.get("/api/stations")
def stations() -> list[dict]:
    latest = db.latest_by_station()
    return [station_view(s, latest.get(s["id"])) for s in STATIONS]


@app.get("/api/stations/{station_id}")
def station(station_id: str) -> dict:
    if station_id not in STATION_IDS:
        raise HTTPException(404, f"unknown station '{station_id}'")
    s = next(s for s in STATIONS if s["id"] == station_id)
    return station_view(s, db.latest_by_station().get(station_id))


@app.get("/api/stations/{station_id}/readings")
def station_readings(station_id: str, hours: int = Query(72, ge=1, le=24 * 30)) -> list[dict]:
    if station_id not in STATION_IDS:
        raise HTTPException(404, f"unknown station '{station_id}'")
    return [quality.score(r) for r in db.history(station_id, hours)]


@app.get("/api/summary")
def summary() -> dict:
    latest = [quality.score(r) for r in db.latest_by_station().values()]
    counts = {b["key"]: 0 for b in STATUS_BANDS}
    for r in latest:
        counts[r["status"]] += 1
    worst = max(latest, key=lambda r: r["index"], default=None)
    return {
        "stations": len(STATIONS),
        "reporting": len(latest),
        "status_counts": counts,
        "average_index": round(sum(r["index"] for r in latest) / len(latest), 2) if latest else None,
        "worst": {"station_id": worst["station_id"], "index": worst["index"]} if worst else None,
        "alerts_24h": len(quality.alerts(db.history(hours=24))),
    }


@app.get("/api/alerts")
def alerts(hours: int = Query(24, ge=1, le=24 * 30),
           min_status: str = Query("moderate", pattern="^(light|moderate|heavy)$")) -> list[dict]:
    return quality.alerts(db.history(hours=hours), min_status)[:200]


@app.post("/api/readings", status_code=201)
def ingest(reading: ReadingIn, x_api_key: str | None = Header(None)) -> dict:
    """Store a reading from a real sensor or lab and return its score."""
    key = os.environ.get("WQ_API_KEY")
    if key and x_api_key != key:
        raise HTTPException(401, "invalid or missing X-API-Key")
    row = reading.model_dump()
    row["timestamp"] = row["timestamp"] or datetime.now(timezone.utc)
    db.insert_readings([row])
    return quality.score({**row, "timestamp": db.to_iso(row["timestamp"])})


if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
