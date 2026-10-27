from datetime import datetime, timedelta, timezone
from statistics import mean

from app import db, simulator
from app.config import STATIONS


def test_generate_covers_every_station_and_hour():
    end = datetime(2026, 10, 26, tzinfo=timezone.utc)
    rows = simulator.generate(end - timedelta(hours=23), end, seed=1)
    assert len(rows) == 24 * len(STATIONS)


def test_values_stay_physically_plausible():
    end = datetime(2026, 10, 26, tzinfo=timezone.utc)
    for r in simulator.generate(end - timedelta(days=7), end, seed=2):
        assert 0 <= r["ph"] <= 14
        assert r["do"] > 0
        assert r["bod"] > 0 and r["cod"] > 0 and r["tss"] > 0
        assert 15 < r["temperature"] < 40


def test_industrial_rivers_are_dirtier_than_headwaters():
    end = datetime(2026, 10, 26, tzinfo=timezone.utc)
    rows = simulator.generate(end - timedelta(days=3), end, seed=3)
    bod = {sid: mean(r["bod"] for r in rows if r["station_id"] == sid) for sid in ("cisanti", "majalaya")}
    assert bod["majalaya"] > 3 * bod["cisanti"]


def test_backfill_stores_readings():
    n = simulator.backfill(hours=6)
    assert n == 7 * len(STATIONS)
    assert db.count() == n
    assert set(db.latest_by_station()) == {s["id"] for s in STATIONS}
