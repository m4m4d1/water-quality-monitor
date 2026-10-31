from fastapi.testclient import TestClient

from app.main import app

GOOD = {"station_id": "cisanti", "ph": 7.2, "do": 7.4, "bod": 1.2, "cod": 7, "tss": 12, "temperature": 23.5}


def test_ingest_scores_and_stores_a_reading():
    with TestClient(app) as c:
        res = c.post("/api/readings", json=GOOD)
        assert res.status_code == 201
        assert res.json()["status"] == "good"
        latest = c.get("/api/stations/cisanti").json()["latest"]
        assert latest["bod"] == 1.2


def test_ingest_flags_polluted_water():
    with TestClient(app) as c:
        res = c.post("/api/readings", json={**GOOD, "station_id": "majalaya", "do": 0.8, "bod": 80,
                                            "cod": 400, "tss": 400})
        body = res.json()
        assert body["status"] in {"moderate", "heavy"}
        assert {"do", "bod", "cod", "tss"} <= {e["parameter"] for e in body["exceedances"]}


def test_ingest_validates_input():
    with TestClient(app) as c:
        assert c.post("/api/readings", json={**GOOD, "station_id": "nowhere"}).status_code == 422
        assert c.post("/api/readings", json={**GOOD, "ph": 15}).status_code == 422
        assert c.post("/api/readings", json={"station_id": "cisanti"}).status_code == 422


def test_api_key_is_enforced_when_set(monkeypatch):
    monkeypatch.setenv("WQ_API_KEY", "secret")
    with TestClient(app) as c:
        assert c.post("/api/readings", json=GOOD).status_code == 401
        assert c.post("/api/readings", json=GOOD, headers={"X-API-Key": "secret"}).status_code == 201
