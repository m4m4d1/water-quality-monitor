"""Monitoring stations, measured parameters and quality limits.

Limits follow the Class II river water quality standard (baku mutu air sungai kelas II)
in Indonesian Government Regulation PP No. 22/2021, Annex VI. Class II water is meant
for recreation, freshwater fish farming, livestock and irrigation. Check the regulation
before using these values for official purposes.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("WQ_DB", ROOT / "data" / "water.db"))

# Station profiles drive the simulator: how polluted the water usually is.
#   clean      headwaters and reservoirs
#   urban      rivers through cities (domestic waste)
#   industrial rivers next to textile and other factories
STATIONS = [
    {"id": "cisanti", "name": "Situ Cisanti", "river": "Citarum", "province": "Jawa Barat",
     "lat": -7.208, "lon": 107.657, "profile": "clean"},
    {"id": "majalaya", "name": "Majalaya", "river": "Citarum", "province": "Jawa Barat",
     "lat": -7.045, "lon": 107.752, "profile": "industrial"},
    {"id": "dayeuhkolot", "name": "Dayeuhkolot", "river": "Citarum", "province": "Jawa Barat",
     "lat": -6.987, "lon": 107.625, "profile": "industrial"},
    {"id": "nanjung", "name": "Nanjung", "river": "Citarum", "province": "Jawa Barat",
     "lat": -6.944, "lon": 107.534, "profile": "industrial"},
    {"id": "jatiluhur", "name": "Waduk Jatiluhur", "river": "Citarum", "province": "Jawa Barat",
     "lat": -6.530, "lon": 107.380, "profile": "clean"},
    {"id": "karawang", "name": "Karawang", "river": "Citarum", "province": "Jawa Barat",
     "lat": -6.300, "lon": 107.300, "profile": "urban"},
    {"id": "manggarai", "name": "Pintu Air Manggarai", "river": "Ciliwung", "province": "DKI Jakarta",
     "lat": -6.208, "lon": 106.850, "profile": "urban"},
    {"id": "gunungsari", "name": "Gunungsari", "river": "Kali Surabaya (Brantas)", "province": "Jawa Timur",
     "lat": -7.300, "lon": 112.710, "profile": "urban"},
    {"id": "musi", "name": "Palembang", "river": "Musi", "province": "Sumatera Selatan",
     "lat": -2.990, "lon": 104.760, "profile": "urban"},
    {"id": "kapuas", "name": "Pontianak", "river": "Kapuas", "province": "Kalimantan Barat",
     "lat": -0.030, "lon": 109.330, "profile": "clean"},
    {"id": "mahakam", "name": "Samarinda", "river": "Mahakam", "province": "Kalimantan Timur",
     "lat": -0.500, "lon": 117.150, "profile": "urban"},
]
STATION_IDS = {s["id"] for s in STATIONS}

# kind: "max" = must stay below the limit, "min" = must stay above it,
# "range" = must stay between low and high, "info" = shown but not scored.
PARAMETERS = {
    "ph": {"en": "pH", "id": "pH", "unit": "", "kind": "range", "low": 6.0, "high": 9.0},
    "do": {"en": "Dissolved oxygen", "id": "Oksigen terlarut", "unit": "mg/L", "kind": "min", "limit": 4.0},
    "bod": {"en": "BOD", "id": "BOD", "unit": "mg/L", "kind": "max", "limit": 3.0},
    "cod": {"en": "COD", "id": "COD", "unit": "mg/L", "kind": "max", "limit": 25.0},
    "tss": {"en": "Suspended solids", "id": "Padatan tersuspensi", "unit": "mg/L", "kind": "max", "limit": 50.0},
    "temperature": {"en": "Temperature", "id": "Suhu", "unit": "°C", "kind": "info"},
}
SCORED = [k for k, p in PARAMETERS.items() if p["kind"] != "info"]

# Pollution index (Indeks Pencemaran) bands, from KepMenLH No. 115/2003.
STATUS_BANDS = [
    {"key": "good", "max": 1.0, "en": "Meets standard", "id": "Memenuhi baku mutu", "color": "#1f9d6b"},
    {"key": "light", "max": 5.0, "en": "Lightly polluted", "id": "Cemar ringan", "color": "#d9a400"},
    {"key": "moderate", "max": 10.0, "en": "Moderately polluted", "id": "Cemar sedang", "color": "#e46b1f"},
    {"key": "heavy", "max": float("inf"), "en": "Heavily polluted", "id": "Cemar berat", "color": "#c8102e"},
]
