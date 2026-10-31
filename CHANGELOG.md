# Changelog

## Unreleased

- Dockerfile, tests for the sensor ingest endpoint and API key, and full documentation.
- Station map (colour by status) and a 24-hour alerts panel linked to the station detail.
- Bilingual (EN/ID) dashboard: summary, station table, station detail with 72-hour chart.
- REST API: stations, history, summary, alerts and a sensor ingest endpoint (`/docs` for details).
- Pollution index (Indeks Pencemaran, KepMenLH 115/2003) with status bands and Class II limit checks.
- Sensor data simulator with daily cycles and pollution events, and SQLite storage
  (`python -m app.simulator --hours 72`).
- Project scaffold, 11 monitoring stations and the water quality data model (Class II limits, PP 22/2021).
