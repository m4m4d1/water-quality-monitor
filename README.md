# Water Quality Monitoring System

**Sistem Pemantauan Kualitas Air** for Indonesian rivers.

Monitors river water quality at stations along the Citarum and other Indonesian rivers, scores each
reading with the national pollution index (*Indeks Pencemaran*), and raises alerts when a river
breaks the Class II standard of PP 22/2021.

> Week 1 of Nusantara Intel: one new open-source
> information system for Indonesia every week, built in public one step per day.

## Features

- **11 stations**: six along the Citarum (from the source at Situ Cisanti to Karawang), plus the
  Ciliwung in Jakarta, Kali Surabaya, the Musi, the Kapuas and the Mahakam.
- **Pollution index** per KepMenLH 115/2003 with four bands: meets standard, lightly, moderately
  and heavily polluted.
- **Alerts** when a station reaches "moderately polluted", listing which limits were broken.
- **Bilingual dashboard** (English / Bahasa Indonesia): summary, station table, 72-hour charts,
  map and alerts.
- **REST API** with interactive docs at `/docs`, including an endpoint for real sensors.
- **Simulator** that produces realistic readings (daily oxygen and temperature cycles, pollution
  events) so the system runs out of the box.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000 for the dashboard and http://localhost:8000/docs for the API.
On first start the database is filled with 72 hours of simulated readings, and a new reading per
station is added every minute.

With Docker:

```bash
docker build -t water-quality-monitor .
docker run -p 8000:8000 -v wq-data:/data water-quality-monitor
```

## Configuration

| Variable | Default | Meaning |
|----------|---------|---------|
| `WQ_DB` | `data/water.db` | SQLite database file |
| `WQ_SIMULATE` | `1` | `0` turns the simulator off (use with real sensors) |
| `WQ_SIM_INTERVAL` | `60` | Seconds between simulated readings |
| `WQ_API_KEY` | not set | If set, `POST /api/readings` needs the header `X-API-Key` |

## API

| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/stations` | All stations with their latest scored reading |
| GET | `/api/stations/{id}/readings?hours=72` | History for one station |
| GET | `/api/summary` | Counts per status, average index, worst station |
| GET | `/api/alerts?hours=24&min_status=moderate` | Readings at or above a status |
| GET | `/api/meta` | Parameters, limits and status bands |
| POST | `/api/readings` | Store a reading from a sensor or lab; returns its score |

Send a reading from a real sensor:

```bash
curl -X POST http://localhost:8000/api/readings \
  -H "Content-Type: application/json" \
  -d '{"station_id": "dayeuhkolot", "ph": 7.4, "do": 3.1, "bod": 9.5, "cod": 41, "tss": 88, "temperature": 27.9}'
```

## How water quality is scored

| Parameter | Unit | Class II limit (PP 22/2021) |
|-----------|------|-----------------------------|
| pH | | 6 to 9 |
| Dissolved oxygen (DO) | mg/L | at least 4 |
| BOD | mg/L | at most 3 |
| COD | mg/L | at most 25 |
| Total suspended solids (TSS) | mg/L | at most 50 |
| Temperature | °C | shown, not scored |

For each parameter the measured value is divided by its limit (oxygen and pH use the
KepMenLH 115/2003 variants). Ratios above 1 are dampened as `1 + 5·log10(ratio)`, and the index is
`sqrt((max² + mean²) / 2)`:

| Index | Status |
|-------|--------|
| 0 to 1 | Meets standard (*memenuhi baku mutu*) |
| 1 to 5 | Lightly polluted (*cemar ringan*) |
| 5 to 10 | Moderately polluted (*cemar sedang*) |
| above 10 | Heavily polluted (*cemar berat*) |

## Tests

```bash
pytest -q
```

## Notes

The demo data is simulated: station locations are real, readings are not. Check the regulations
before using the limits for official purposes.

## Roadmap this week

- [x] Mon: scaffold, stations and data model
- [x] Tue: sensor data simulator and storage
- [x] Wed: REST API, pollution index and alerts
- [x] Thu: dashboard
- [x] Fri: map and alerts panel
- [x] Sat: Docker, tests and documentation
- [ ] Sun: live demo and v1.0 release

## License

MIT
