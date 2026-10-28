"""Pollution index (Indeks Pencemaran, KepMenLH No. 115/2003) and alerts.

For each scored parameter we compute the ratio between the measured value and
its limit (above 1 means the limit is broken). Ratios above 1 are dampened as
1 + 5·log10(ratio). The index combines the worst and the average ratio:

    PI = sqrt((max_ratio² + mean_ratio²) / 2)

0-1 meets the standard, 1-5 is lightly polluted, 5-10 moderately and above 10
heavily polluted.
"""
import math

from .config import PARAMETERS, SCORED, STATUS_BANDS


def do_saturation(temperature: float) -> float:
    """Oxygen saturation in fresh water (mg/L) at a given temperature (°C)."""
    t = temperature
    return 14.652 - 0.41022 * t + 0.007991 * t ** 2 - 0.000077774 * t ** 3


def ratio(param: str, value: float, temperature: float = 28.0) -> float:
    spec = PARAMETERS[param]
    if spec["kind"] == "max":
        r = value / spec["limit"]
    elif spec["kind"] == "min":
        # Less oxygen is worse: compare the gap to saturation with the allowed gap.
        sat = max(do_saturation(temperature), spec["limit"] + 0.5)
        r = max(0.0, sat - value) / (sat - spec["limit"])
    else:  # range
        mid = (spec["low"] + spec["high"]) / 2
        edge = spec["low"] if value <= mid else spec["high"]
        r = (value - mid) / (edge - mid)
    return 1 + 5 * math.log10(r) if r > 1 else r


def pollution_index(reading: dict) -> float:
    ratios = [ratio(p, reading[p], reading.get("temperature", 28.0)) for p in SCORED]
    worst, avg = max(ratios), sum(ratios) / len(ratios)
    return round(math.sqrt((worst ** 2 + avg ** 2) / 2), 2)


def status(index: float) -> dict:
    return next(b for b in STATUS_BANDS if index <= b["max"])


def exceedances(reading: dict) -> list[dict]:
    """Parameters that break their Class II limit in this reading."""
    out = []
    for p in SCORED:
        spec, value = PARAMETERS[p], reading[p]
        broken = ((spec["kind"] == "max" and value > spec["limit"])
                  or (spec["kind"] == "min" and value < spec["limit"])
                  or (spec["kind"] == "range" and not spec["low"] <= value <= spec["high"]))
        if broken:
            limit = spec.get("limit", f"{spec.get('low')}-{spec.get('high')}")
            out.append({"parameter": p, "value": value, "limit": limit, "unit": spec["unit"]})
    return out


def score(reading: dict) -> dict:
    """A reading with its index, status and broken limits attached."""
    index = pollution_index(reading)
    band = status(index)
    return {**reading, "index": index, "status": band["key"],
            "status_label": {"en": band["en"], "id": band["id"]},
            "exceedances": exceedances(reading)}


def alerts(readings: list[dict], min_status: str = "moderate") -> list[dict]:
    """Readings at or above `min_status`, newest first."""
    order = [b["key"] for b in STATUS_BANDS]
    threshold = order.index(min_status)
    scored = (score(r) for r in readings)
    hits = [r for r in scored if order.index(r["status"]) >= threshold]
    return sorted(hits, key=lambda r: r["timestamp"], reverse=True)
