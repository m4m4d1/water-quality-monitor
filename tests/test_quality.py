import pytest

from app import quality

CLEAN = {"ph": 7.3, "do": 7.2, "bod": 1.5, "cod": 8.0, "tss": 15.0, "temperature": 25.0}
DIRTY = {"ph": 8.9, "do": 1.0, "bod": 40.0, "cod": 180.0, "tss": 300.0, "temperature": 29.0}


def test_clean_water_meets_standard():
    index = quality.pollution_index(CLEAN)
    assert index <= 1
    assert quality.status(index)["key"] == "good"
    assert quality.exceedances(CLEAN) == []


def test_dirty_water_is_polluted_and_lists_broken_limits():
    scored = quality.score({**DIRTY, "station_id": "majalaya", "timestamp": "2026-10-26T00:00:00+00:00"})
    assert scored["index"] > 5
    assert scored["status"] in {"moderate", "heavy"}
    assert {e["parameter"] for e in scored["exceedances"]} == {"do", "bod", "cod", "tss"}


@pytest.mark.parametrize("value,expected", [(5.5, True), (6.0, False), (9.0, False), (9.4, True)])
def test_ph_range(value, expected):
    broken = any(e["parameter"] == "ph" for e in quality.exceedances({**CLEAN, "ph": value}))
    assert broken is expected


def test_ratio_is_dampened_above_one():
    # BOD of 30 is 10x the limit of 3: 1 + 5 * log10(10) = 6
    assert quality.ratio("bod", 30.0) == pytest.approx(6.0)


def test_index_grows_with_pollution():
    low = quality.pollution_index({**CLEAN, "bod": 4})
    high = quality.pollution_index({**CLEAN, "bod": 40})
    assert high > low


def test_alerts_filters_and_sorts():
    rows = [
        {**CLEAN, "station_id": "cisanti", "timestamp": "2026-10-26T01:00:00+00:00"},
        {**DIRTY, "station_id": "majalaya", "timestamp": "2026-10-26T02:00:00+00:00"},
        {**DIRTY, "station_id": "nanjung", "timestamp": "2026-10-26T03:00:00+00:00"},
    ]
    hits = quality.alerts(rows)
    assert [h["station_id"] for h in hits] == ["nanjung", "majalaya"]
