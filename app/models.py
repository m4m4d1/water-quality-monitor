"""Data model for water quality readings."""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .config import STATION_IDS


class ReadingIn(BaseModel):
    """One set of measurements from a station (sensor or lab)."""

    station_id: str
    timestamp: datetime | None = Field(None, description="Measurement time; defaults to now (UTC)")
    ph: float = Field(..., ge=0, le=14)
    do: float = Field(..., ge=0, le=20, description="Dissolved oxygen, mg/L")
    bod: float = Field(..., ge=0, le=500, description="Biochemical oxygen demand, mg/L")
    cod: float = Field(..., ge=0, le=2000, description="Chemical oxygen demand, mg/L")
    tss: float = Field(..., ge=0, le=5000, description="Total suspended solids, mg/L")
    temperature: float = Field(..., ge=0, le=45, description="Water temperature, °C")

    @field_validator("station_id")
    @classmethod
    def known_station(cls, v: str) -> str:
        if v not in STATION_IDS:
            raise ValueError(f"unknown station '{v}'")
        return v


class Reading(ReadingIn):
    timestamp: datetime
