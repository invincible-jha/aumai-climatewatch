"""Core logic for aumai-climatewatch: climate zones, alert generation, reports."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from .models import ClimateReport, ClimateZone, WeatherAlert

__all__ = ["ClimateZoneRegistry", "AlertGenerator", "ClimateAnalyzer"]

# ---------------------------------------------------------------------------
# India's climate zones (IMD classification)
# ---------------------------------------------------------------------------

_ZONES: list[dict[str, object]] = [
    {
        "zone_id": "northwest-india",
        "name": "Northwest India",
        "states": ["Rajasthan", "Punjab", "Haryana", "Himachal Pradesh", "Jammu & Kashmir", "Ladakh"],
        "avg_rainfall_mm": 350.0,
        "avg_temp_c": 24.0,
    },
    {
        "zone_id": "northeast-india",
        "name": "Northeast India",
        "states": ["Assam", "Meghalaya", "Arunachal Pradesh", "Nagaland", "Manipur", "Mizoram", "Tripura", "Sikkim"],
        "avg_rainfall_mm": 2500.0,
        "avg_temp_c": 22.0,
    },
    {
        "zone_id": "central-india",
        "name": "Central India",
        "states": ["Madhya Pradesh", "Chhattisgarh", "Jharkhand", "Odisha"],
        "avg_rainfall_mm": 1100.0,
        "avg_temp_c": 27.0,
    },
    {
        "zone_id": "western-india",
        "name": "Western India",
        "states": ["Gujarat", "Maharashtra", "Goa"],
        "avg_rainfall_mm": 900.0,
        "avg_temp_c": 27.5,
    },
    {
        "zone_id": "southern-peninsula",
        "name": "Southern Peninsula",
        "states": ["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh", "Telangana"],
        "avg_rainfall_mm": 1200.0,
        "avg_temp_c": 28.0,
    },
    {
        "zone_id": "eastern-india",
        "name": "Eastern India",
        "states": ["West Bengal", "Bihar", "Uttar Pradesh", "Uttarakhand"],
        "avg_rainfall_mm": 1050.0,
        "avg_temp_c": 26.5,
    },
]

# Alert thresholds
_FLOOD_RAINFALL_MM = 200.0        # 24h rainfall for flood watch
_FLOOD_SEVERE_RAINFALL_MM = 400.0 # 24h rainfall for severe flood warning
_DROUGHT_DEFICIT_PCT = 25.0       # % below normal for drought watch
_DROUGHT_SEVERE_PCT = 50.0        # % below normal for severe drought
_HEATWAVE_TEMP_C = 40.0           # temperature threshold for heatwave watch
_SEVERE_HEATWAVE_TEMP_C = 45.0    # severe heatwave
_COLD_WAVE_TEMP_C = 5.0           # cold wave
_CYCLONE_WIND_KMH = 64.0          # tropical storm (Beaufort 8)
_SEVERE_CYCLONE_WIND_KMH = 118.0  # severe cyclonic storm


class ClimateZoneRegistry:
    """Registry of India's major climate zones."""

    def __init__(self) -> None:
        self._zones: dict[str, ClimateZone] = {
            z["zone_id"]: ClimateZone(**z)  # type: ignore[arg-type]
            for z in _ZONES
        }

    def all_zones(self) -> list[ClimateZone]:
        """Return all registered climate zones."""
        return list(self._zones.values())

    def get_zone(self, zone_id: str) -> ClimateZone | None:
        """Lookup a zone by its ID."""
        return self._zones.get(zone_id)

    def zones_for_state(self, state: str) -> list[ClimateZone]:
        """Return zones that include a given state."""
        state_lower = state.lower()
        return [
            z for z in self._zones.values()
            if any(s.lower() == state_lower for s in z.states)
        ]


class AlertGenerator:
    """Generates weather alerts from raw climate observations using rule-based logic."""

    def evaluate_conditions(
        self, zone: ClimateZone, data: dict[str, object]
    ) -> list[WeatherAlert]:
        """Apply threshold rules to observation data and return active alerts."""
        alerts: list[WeatherAlert] = []
        now = datetime.now(tz=timezone.utc)
        valid_until = now + timedelta(hours=24)

        rainfall_mm: float = float(data.get("rainfall_mm", 0.0))
        temperature_c: float = float(data.get("temperature_c", zone.avg_temp_c))
        wind_kmh: float = float(data.get("wind_kmh", 0.0))
        rainfall_deficit_pct: float = float(data.get("rainfall_deficit_pct", 0.0))

        # Flood alerts
        if rainfall_mm >= _FLOOD_SEVERE_RAINFALL_MM:
            alerts.append(WeatherAlert(
                alert_id=str(uuid.uuid4()),
                alert_type="flood",
                severity="severe_warning",
                affected_zones=[zone.zone_id],
                message=(
                    f"SEVERE FLOOD WARNING for {zone.name}. Extremely heavy rainfall of"
                    f" {rainfall_mm:.0f} mm in 24 hours. Evacuate flood-prone areas immediately."
                    " Do not cross flooded waterways."
                ),
                issued_at=now,
                valid_until=valid_until,
            ))
        elif rainfall_mm >= _FLOOD_RAINFALL_MM:
            alerts.append(WeatherAlert(
                alert_id=str(uuid.uuid4()),
                alert_type="flood",
                severity="warning",
                affected_zones=[zone.zone_id],
                message=(
                    f"FLOOD WARNING for {zone.name}. Heavy rainfall of {rainfall_mm:.0f} mm"
                    " expected in 24 hours. Move to higher ground if in low-lying areas."
                ),
                issued_at=now,
                valid_until=valid_until,
            ))

        # Drought alerts
        if rainfall_deficit_pct >= _DROUGHT_SEVERE_PCT:
            alerts.append(WeatherAlert(
                alert_id=str(uuid.uuid4()),
                alert_type="drought",
                severity="severe_warning",
                affected_zones=[zone.zone_id],
                message=(
                    f"SEVERE DROUGHT WARNING for {zone.name}. Rainfall is"
                    f" {rainfall_deficit_pct:.0f}% below normal. Initiate water conservation"
                    " measures and activate drought relief protocols."
                ),
                issued_at=now,
                valid_until=now + timedelta(days=7),
            ))
        elif rainfall_deficit_pct >= _DROUGHT_DEFICIT_PCT:
            alerts.append(WeatherAlert(
                alert_id=str(uuid.uuid4()),
                alert_type="drought",
                severity="watch",
                affected_zones=[zone.zone_id],
                message=(
                    f"DROUGHT WATCH for {zone.name}. Rainfall is"
                    f" {rainfall_deficit_pct:.0f}% below normal. Monitor reservoir levels"
                    " and groundwater conditions."
                ),
                issued_at=now,
                valid_until=now + timedelta(days=7),
            ))

        # Heatwave alerts
        if temperature_c >= _SEVERE_HEATWAVE_TEMP_C:
            alerts.append(WeatherAlert(
                alert_id=str(uuid.uuid4()),
                alert_type="heatwave",
                severity="severe_warning",
                affected_zones=[zone.zone_id],
                message=(
                    f"SEVERE HEATWAVE WARNING for {zone.name}. Temperature {temperature_c:.1f}°C."
                    " Avoid outdoor activities 11 AM - 4 PM. Stay hydrated. Heat stroke risk is EXTREME."
                ),
                issued_at=now,
                valid_until=valid_until,
            ))
        elif temperature_c >= _HEATWAVE_TEMP_C:
            alerts.append(WeatherAlert(
                alert_id=str(uuid.uuid4()),
                alert_type="heatwave",
                severity="warning",
                affected_zones=[zone.zone_id],
                message=(
                    f"HEATWAVE WARNING for {zone.name}. Temperature {temperature_c:.1f}°C."
                    " Limit outdoor exposure during peak hours. Drink water regularly."
                ),
                issued_at=now,
                valid_until=valid_until,
            ))

        # Cold wave
        if temperature_c <= _COLD_WAVE_TEMP_C:
            alerts.append(WeatherAlert(
                alert_id=str(uuid.uuid4()),
                alert_type="cold_wave",
                severity="warning",
                affected_zones=[zone.zone_id],
                message=(
                    f"COLD WAVE WARNING for {zone.name}. Temperature {temperature_c:.1f}°C."
                    " Keep elderly and children indoors. Protect livestock."
                ),
                issued_at=now,
                valid_until=valid_until,
            ))

        # Cyclone alerts
        if wind_kmh >= _SEVERE_CYCLONE_WIND_KMH:
            alerts.append(WeatherAlert(
                alert_id=str(uuid.uuid4()),
                alert_type="cyclone",
                severity="severe_warning",
                affected_zones=[zone.zone_id],
                message=(
                    f"SEVERE CYCLONE WARNING for {zone.name}. Wind speed {wind_kmh:.0f} km/h."
                    " Evacuate coastal areas immediately. Do not go outdoors."
                ),
                issued_at=now,
                valid_until=valid_until,
            ))
        elif wind_kmh >= _CYCLONE_WIND_KMH:
            alerts.append(WeatherAlert(
                alert_id=str(uuid.uuid4()),
                alert_type="cyclone",
                severity="warning",
                affected_zones=[zone.zone_id],
                message=(
                    f"CYCLONE WATCH for {zone.name}. Wind speed {wind_kmh:.0f} km/h."
                    " Secure loose objects. Monitor IMD bulletins."
                ),
                issued_at=now,
                valid_until=valid_until,
            ))

        return alerts


class ClimateAnalyzer:
    """Generates comprehensive climate reports and trend analyses."""

    def __init__(self) -> None:
        self._alert_gen = AlertGenerator()

    def generate_report(
        self, zone: ClimateZone, weather_data: dict[str, object]
    ) -> ClimateReport:
        """Generate a climate report for a zone given current weather observations."""
        alerts = self._alert_gen.evaluate_conditions(zone, weather_data)

        # Build a simple forecast summary from data
        temp = float(weather_data.get("temperature_c", zone.avg_temp_c))
        rainfall = float(weather_data.get("rainfall_mm", 0.0))
        humidity = float(weather_data.get("humidity_pct", 60.0))

        forecast: dict[str, object] = {
            "next_24h": {
                "temperature_c": temp,
                "expected_rainfall_mm": rainfall * 0.8,
                "humidity_pct": humidity,
                "advisory": (
                    "Conditions similar to today expected. Monitor IMD forecasts at mausam.imd.gov.in."
                ),
            },
            "next_7_days": {
                "trend": (
                    "wetter than normal" if rainfall > zone.avg_rainfall_mm / 30
                    else "drier than normal" if rainfall < zone.avg_rainfall_mm / 60
                    else "near normal"
                ),
                "temperature_trend": (
                    "above normal" if temp > zone.avg_temp_c + 3
                    else "below normal" if temp < zone.avg_temp_c - 3
                    else "near normal"
                ),
            },
        }

        return ClimateReport(
            zone=zone,
            current_conditions=dict(weather_data),
            alerts=alerts,
            forecast=forecast,
        )

    def trend_analysis(
        self, zone: ClimateZone, historical: list[dict[str, object]]
    ) -> dict[str, object]:
        """Compute basic trend statistics from a list of historical observations."""
        if not historical:
            return {"error": "No historical data provided."}

        temps = [float(d["temperature_c"]) for d in historical if "temperature_c" in d]
        rains = [float(d["rainfall_mm"]) for d in historical if "rainfall_mm" in d]

        result: dict[str, object] = {
            "zone_id": zone.zone_id,
            "zone_name": zone.name,
            "observations": len(historical),
        }

        if temps:
            result["temperature"] = {
                "mean_c": round(sum(temps) / len(temps), 2),
                "min_c": round(min(temps), 2),
                "max_c": round(max(temps), 2),
                "anomaly_vs_normal_c": round(sum(temps) / len(temps) - zone.avg_temp_c, 2),
            }

        if rains:
            total_rain = sum(rains)
            expected_rain = zone.avg_rainfall_mm * len(rains) / 365.0
            result["rainfall"] = {
                "total_mm": round(total_rain, 2),
                "mean_daily_mm": round(total_rain / len(rains), 2),
                "deficit_vs_normal_pct": round(
                    (1 - total_rain / expected_rain) * 100 if expected_rain > 0 else 0.0, 2
                ),
            }

        return result
