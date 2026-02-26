"""Pydantic v2 models for aumai-climatewatch climate monitoring."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

__all__ = ["ClimateZone", "WeatherAlert", "ClimateReport"]


class ClimateZone(BaseModel):
    """One of India's major climate zones."""

    zone_id: str = Field(..., description="Unique identifier for the zone")
    name: str = Field(..., description="Human-readable zone name")
    states: list[str] = Field(..., description="States falling within this zone")
    avg_rainfall_mm: float = Field(..., ge=0.0, description="Average annual rainfall in mm")
    avg_temp_c: float = Field(..., description="Average annual temperature in Celsius")


class WeatherAlert(BaseModel):
    """An early-warning alert for extreme weather or climate event."""

    alert_id: str = Field(..., description="Unique alert identifier")
    alert_type: str = Field(
        ...,
        description="Type of alert: flood, drought, cyclone, or heatwave",
        pattern="^(flood|drought|cyclone|heatwave|cold_wave|thunderstorm)$",
    )
    severity: str = Field(
        ...,
        description="Alert severity: watch, warning, or severe_warning",
        pattern="^(watch|warning|severe_warning)$",
    )
    affected_zones: list[str] = Field(
        ..., description="Zone IDs affected by this alert"
    )
    message: str = Field(..., description="Human-readable alert message")
    issued_at: datetime = Field(..., description="Timestamp when alert was issued")
    valid_until: datetime = Field(..., description="Timestamp when alert expires")


class ClimateReport(BaseModel):
    """Comprehensive climate report for a zone at a point in time."""

    zone: ClimateZone
    current_conditions: dict[str, object] = Field(
        ..., description="Current weather measurements keyed by parameter"
    )
    alerts: list[WeatherAlert] = Field(
        default_factory=list, description="Active weather alerts for this zone"
    )
    forecast: dict[str, object] = Field(
        default_factory=dict, description="Short-range forecast summary"
    )
