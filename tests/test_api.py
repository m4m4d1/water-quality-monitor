from fastapi.testclient import TestClient

from app import simulator
from app.config import STATIONS
from app.main import app


def client() -> TestClient:
    simulator.backfill(hours=24)
    return TestClient(app)


def test_health():
    with client() as c:
        body = c.get("/api/health").json()
        assert body["status"] == "ok"
        assert body["readings"] == 25 * len(STATIONS)


def test_stations_have_scored_latest_reading():
    with client() as c:
        stations = c.get("/api/stations").json()
        assert len(stations) == len(STATIONS)
        for s in stations:
            assert s["latest"]["status"] in {"good", "light", "moderate", "heavy"}
            assert s["latest"]["index"] >= 0


def test_station_history_and_unknown_station():
    with client() as c:
        rows = c.get("/api/stations/majalaya/readings?hours=12").json()
        assert 12 <= len(rows) <= 13
        assert all(r["station_id"] == "majalaya" for r in rows)
        assert c.get("/api/stations/nowhere/readings").status_code == 404


def test_summary_counts_every_reporting_station():
    with client() as c:
        body = c.get("/api/summary").json()
        assert body["reporting"] == len(STATIONS)
        assert sum(body["status_counts"].values()) == len(STATIONS)
        assert body["worst"]["index"] >= body["average_index"]


def test_alerts_endpoint():
    with client() as c:
        alerts = c.get("/api/alerts?hours=24&min_status=light").json()
        assert all(a["status"] in {"light", "moderate", "heavy"} for a in alerts)
        assert c.get("/api/alerts?min_status=bogus").status_code == 422
