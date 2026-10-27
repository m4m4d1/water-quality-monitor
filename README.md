# Water Quality Monitoring System

**Sistem Pemantauan Kualitas Air** for Indonesian rivers.

Monitors river water quality at stations along the Citarum and other Indonesian rivers, scores each
reading with the national pollution index (*Indeks Pencemaran*), and raises alerts when a river
breaks the Class II standard of PP 22/2021.

> Week 1 of Nusantara Intel: one new open-source
> information system for Indonesia every week, built in public one step per day.

## Monitored stations

11 stations: six along the Citarum (from the source at Situ Cisanti to Karawang), plus the
Ciliwung in Jakarta, Kali Surabaya, the Musi, the Kapuas and the Mahakam.

## Parameters

| Parameter | Unit | Class II limit |
|-----------|------|----------------|
| pH | | 6 to 9 |
| Dissolved oxygen (DO) | mg/L | at least 4 |
| BOD | mg/L | at most 3 |
| COD | mg/L | at most 25 |
| Total suspended solids (TSS) | mg/L | at most 50 |
| Temperature | °C | shown, not scored |

## Roadmap this week

- [x] Mon: scaffold, stations and data model
- [x] Tue: sensor data simulator and storage
- [ ] Wed: REST API, pollution index and alerts
- [ ] Thu: dashboard
- [ ] Fri: map and alerts panel
- [ ] Sat: Docker, tests and documentation
- [ ] Sun: live demo and v1.0 release

## License

MIT
