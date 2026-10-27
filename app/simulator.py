"""Realistic simulated readings for every station.

Each station profile has typical levels. On top of that the simulator adds a
daily cycle (warmer water and more oxygen in the afternoon from algae
photosynthesis), random sensor noise, and occasional pollution events such as
an untreated factory discharge, which push BOD, COD and suspended solids up
and oxygen down for a few hours.

    python -m app.simulator --hours 72      # fill the database with 3 days of readings
"""
import argparse
import math
import random
from datetime import datetime, timedelta, timezone

from . import db
from .config import STATIONS

PROFILES = {
    #             ph    do   bod   cod   tss  temp
    "clean":      (7.2, 7.0, 1.6, 9.0, 18.0, 24.0),
    "urban":      (7.0, 4.2, 6.5, 32.0, 65.0, 28.5),
    "industrial": (7.6, 2.2, 18.0, 85.0, 130.0, 27.5),
}
EVENT_CHANCE = {"clean": 0.003, "urban": 0.02, "industrial": 0.04}  # per reading
EVENT_HOURS = (3, 9)


def _event_strength(station_id: str, ts: datetime, profile: str) -> float:
    """0 when no pollution event is active, up to ~1 at the peak of one.

    Events are derived from a hash of (station, hour) so that the same time
    always gives the same answer, whichever order readings are generated in.
    """
    strength = 0.0
    for back in range(EVENT_HOURS[1]):
        hour = (ts - timedelta(hours=back)).replace(minute=0, second=0, microsecond=0)
        rng = random.Random(f"{station_id}:{hour.isoformat()}")
        if rng.random() < EVENT_CHANCE[profile]:
            length = rng.randint(*EVENT_HOURS)
            if back < length:
                strength = max(strength, math.sin(math.pi * (back + 0.5) / length) * rng.uniform(0.6, 1.0))
    return strength


def reading(station: dict, ts: datetime, rng: random.Random) -> dict:
    ph, do, bod, cod, tss, temp = PROFILES[station["profile"]]
    local_hour = (ts.hour + 7) % 24  # WIB
    daily = math.sin((local_hour - 9) / 24 * 2 * math.pi)  # peaks mid-afternoon
    event = _event_strength(station["id"], ts, station["profile"])

    temperature = temp + 1.5 * daily + rng.gauss(0, 0.3)
    do_value = do * (1 + 0.18 * daily) * (1 - 0.6 * event) + rng.gauss(0, 0.25)
    return {
        "station_id": station["id"],
        "timestamp": ts,
        "ph": round(min(14, max(0, ph + 0.15 * daily - 0.8 * event + rng.gauss(0, 0.08))), 2),
        "do": round(max(0.1, do_value), 2),
        "bod": round(max(0.2, bod * (1 + 2.5 * event) * rng.lognormvariate(0, 0.12)), 2),
        "cod": round(max(1.0, cod * (1 + 2.2 * event) * rng.lognormvariate(0, 0.12)), 1),
        "tss": round(max(1.0, tss * (1 + 1.8 * event) * rng.lognormvariate(0, 0.18)), 1),
        "temperature": round(temperature, 1),
    }


def generate(start: datetime, end: datetime, step_minutes: int = 60, seed: int | None = None) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    ts = start.replace(second=0, microsecond=0)
    while ts <= end:
        rows.extend(reading(s, ts, rng) for s in STATIONS)
        ts += timedelta(minutes=step_minutes)
    return rows


def backfill(hours: int = 72, step_minutes: int = 60, seed: int | None = 42) -> int:
    """Store `hours` of history ending now."""
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    db.init_db()
    return db.insert_readings(generate(end - timedelta(hours=hours), end, step_minutes, seed))


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill the database with simulated readings.")
    parser.add_argument("--hours", type=int, default=72)
    parser.add_argument("--step", type=int, default=60, help="minutes between readings")
    args = parser.parse_args()
    n = backfill(args.hours, args.step)
    print(f"stored {n} readings in {db.db_path()}")


if __name__ == "__main__":
    main()
