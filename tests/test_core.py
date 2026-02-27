"""Comprehensive tests for aumai-climatewatch core module."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from aumai_climatewatch.core import AlertGenerator, ClimateAnalyzer, ClimateZoneRegistry
from aumai_climatewatch.models import ClimateReport, ClimateZone, WeatherAlert


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def registry() -> ClimateZoneRegistry:
    return ClimateZoneRegistry()


@pytest.fixture()
def alert_gen() -> AlertGenerator:
    return AlertGenerator()


@pytest.fixture()
def analyzer() -> ClimateAnalyzer:
    return ClimateAnalyzer()


@pytest.fixture()
def central_india(registry: ClimateZoneRegistry) -> ClimateZone:
    zone = registry.get_zone("central-india")
    assert zone is not None
    return zone


@pytest.fixture()
def northwest_india(registry: ClimateZoneRegistry) -> ClimateZone:
    zone = registry.get_zone("northwest-india")
    assert zone is not None
    return zone


@pytest.fixture()
def southern_peninsula(registry: ClimateZoneRegistry) -> ClimateZone:
    zone = registry.get_zone("southern-peninsula")
    assert zone is not None
    return zone


@pytest.fixture()
def normal_conditions(central_india: ClimateZone) -> dict[str, object]:
    return {
        "temperature_c": central_india.avg_temp_c,
        "rainfall_mm": 10.0,
        "humidity_pct": 60.0,
        "wind_kmh": 15.0,
        "rainfall_deficit_pct": 5.0,
    }


# ---------------------------------------------------------------------------
# ClimateZone model tests
# ---------------------------------------------------------------------------


class TestClimateZoneModel:
    def test_valid_climate_zone(self) -> None:
        zone = ClimateZone(
            zone_id="test-zone",
            name="Test Zone",
            states=["State A", "State B"],
            avg_rainfall_mm=1000.0,
            avg_temp_c=25.0,
        )
        assert zone.zone_id == "test-zone"
        assert len(zone.states) == 2

    def test_negative_rainfall_raises(self) -> None:
        with pytest.raises(ValidationError):
            ClimateZone(
                zone_id="bad-zone",
                name="Bad",
                states=["X"],
                avg_rainfall_mm=-10.0,
                avg_temp_c=25.0,
            )

    def test_zero_rainfall_valid(self) -> None:
        zone = ClimateZone(
            zone_id="desert",
            name="Desert",
            states=["Rajasthan"],
            avg_rainfall_mm=0.0,
            avg_temp_c=35.0,
        )
        assert zone.avg_rainfall_mm == 0.0

    def test_negative_temperature_valid(self) -> None:
        zone = ClimateZone(
            zone_id="himalaya",
            name="Himalaya",
            states=["Ladakh"],
            avg_rainfall_mm=200.0,
            avg_temp_c=-5.0,
        )
        assert zone.avg_temp_c == -5.0


# ---------------------------------------------------------------------------
# WeatherAlert model tests
# ---------------------------------------------------------------------------


class TestWeatherAlertModel:
    def test_valid_flood_alert(self) -> None:
        now = datetime.now(tz=timezone.utc)
        alert = WeatherAlert(
            alert_id="test-id",
            alert_type="flood",
            severity="warning",
            affected_zones=["central-india"],
            message="Heavy rainfall expected.",
            issued_at=now,
            valid_until=now,
        )
        assert alert.alert_type == "flood"
        assert alert.severity == "warning"

    def test_invalid_alert_type_raises(self) -> None:
        now = datetime.now(tz=timezone.utc)
        with pytest.raises(ValidationError):
            WeatherAlert(
                alert_id="bad",
                alert_type="earthquake",
                severity="warning",
                affected_zones=["test"],
                message="Bad type",
                issued_at=now,
                valid_until=now,
            )

    def test_invalid_severity_raises(self) -> None:
        now = datetime.now(tz=timezone.utc)
        with pytest.raises(ValidationError):
            WeatherAlert(
                alert_id="bad",
                alert_type="flood",
                severity="critical",  # not in pattern
                affected_zones=["test"],
                message="Bad severity",
                issued_at=now,
                valid_until=now,
            )

    def test_all_valid_alert_types(self) -> None:
        now = datetime.now(tz=timezone.utc)
        valid_types = ["flood", "drought", "cyclone", "heatwave", "cold_wave", "thunderstorm"]
        for alert_type in valid_types:
            alert = WeatherAlert(
                alert_id="id",
                alert_type=alert_type,
                severity="watch",
                affected_zones=["test"],
                message="Test",
                issued_at=now,
                valid_until=now,
            )
            assert alert.alert_type == alert_type

    def test_all_valid_severities(self) -> None:
        now = datetime.now(tz=timezone.utc)
        for severity in ["watch", "warning", "severe_warning"]:
            alert = WeatherAlert(
                alert_id="id",
                alert_type="flood",
                severity=severity,
                affected_zones=["test"],
                message="Test",
                issued_at=now,
                valid_until=now,
            )
            assert alert.severity == severity


# ---------------------------------------------------------------------------
# ClimateZoneRegistry tests
# ---------------------------------------------------------------------------


class TestClimateZoneRegistry:
    def test_all_zones_returns_6_zones(self, registry: ClimateZoneRegistry) -> None:
        assert len(registry.all_zones()) == 6

    def test_all_zones_are_climate_zone_objects(
        self, registry: ClimateZoneRegistry
    ) -> None:
        for zone in registry.all_zones():
            assert isinstance(zone, ClimateZone)

    def test_get_zone_central_india_found(
        self, registry: ClimateZoneRegistry
    ) -> None:
        zone = registry.get_zone("central-india")
        assert zone is not None
        assert zone.zone_id == "central-india"

    def test_get_zone_northwest_india_found(
        self, registry: ClimateZoneRegistry
    ) -> None:
        zone = registry.get_zone("northwest-india")
        assert zone is not None

    def test_get_zone_northeast_india_found(
        self, registry: ClimateZoneRegistry
    ) -> None:
        assert registry.get_zone("northeast-india") is not None

    def test_get_zone_western_india_found(
        self, registry: ClimateZoneRegistry
    ) -> None:
        assert registry.get_zone("western-india") is not None

    def test_get_zone_southern_peninsula_found(
        self, registry: ClimateZoneRegistry
    ) -> None:
        assert registry.get_zone("southern-peninsula") is not None

    def test_get_zone_eastern_india_found(
        self, registry: ClimateZoneRegistry
    ) -> None:
        assert registry.get_zone("eastern-india") is not None

    def test_get_zone_unknown_returns_none(
        self, registry: ClimateZoneRegistry
    ) -> None:
        assert registry.get_zone("atlantis") is None

    def test_zones_for_state_rajasthan_in_northwest(
        self, registry: ClimateZoneRegistry
    ) -> None:
        zones = registry.zones_for_state("Rajasthan")
        assert len(zones) == 1
        assert zones[0].zone_id == "northwest-india"

    def test_zones_for_state_case_insensitive(
        self, registry: ClimateZoneRegistry
    ) -> None:
        upper = registry.zones_for_state("RAJASTHAN")
        lower = registry.zones_for_state("rajasthan")
        assert len(upper) == len(lower)

    def test_zones_for_state_unknown_returns_empty(
        self, registry: ClimateZoneRegistry
    ) -> None:
        assert registry.zones_for_state("Narnia") == []

    def test_zones_for_state_karnataka_in_southern(
        self, registry: ClimateZoneRegistry
    ) -> None:
        zones = registry.zones_for_state("Karnataka")
        assert any(z.zone_id == "southern-peninsula" for z in zones)

    def test_zones_for_state_assam_in_northeast(
        self, registry: ClimateZoneRegistry
    ) -> None:
        zones = registry.zones_for_state("Assam")
        assert any(z.zone_id == "northeast-india" for z in zones)

    def test_all_zones_have_at_least_one_state(
        self, registry: ClimateZoneRegistry
    ) -> None:
        for zone in registry.all_zones():
            assert len(zone.states) > 0

    def test_all_zones_have_positive_avg_temp(
        self, registry: ClimateZoneRegistry
    ) -> None:
        for zone in registry.all_zones():
            assert zone.avg_temp_c > 0

    def test_all_zones_have_positive_avg_rainfall(
        self, registry: ClimateZoneRegistry
    ) -> None:
        for zone in registry.all_zones():
            assert zone.avg_rainfall_mm >= 0


# ---------------------------------------------------------------------------
# AlertGenerator tests
# ---------------------------------------------------------------------------


class TestAlertGenerator:
    def test_no_alerts_for_normal_conditions(
        self,
        alert_gen: AlertGenerator,
        central_india: ClimateZone,
        normal_conditions: dict[str, object],
    ) -> None:
        alerts = alert_gen.evaluate_conditions(central_india, normal_conditions)
        assert alerts == []

    def test_flood_warning_at_200mm_threshold(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"rainfall_mm": 200.0, "temperature_c": 27.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        flood_alerts = [a for a in alerts if a.alert_type == "flood"]
        assert len(flood_alerts) == 1
        assert flood_alerts[0].severity == "warning"

    def test_severe_flood_warning_at_400mm(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"rainfall_mm": 400.0, "temperature_c": 27.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        flood_alerts = [a for a in alerts if a.alert_type == "flood"]
        assert len(flood_alerts) == 1
        assert flood_alerts[0].severity == "severe_warning"

    def test_no_flood_alert_below_threshold(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"rainfall_mm": 100.0, "temperature_c": 27.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        assert not any(a.alert_type == "flood" for a in alerts)

    def test_drought_watch_at_25pct_deficit(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"rainfall_deficit_pct": 25.0, "temperature_c": 27.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        drought_alerts = [a for a in alerts if a.alert_type == "drought"]
        assert len(drought_alerts) == 1
        assert drought_alerts[0].severity == "watch"

    def test_severe_drought_at_50pct_deficit(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"rainfall_deficit_pct": 50.0, "temperature_c": 27.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        drought_alerts = [a for a in alerts if a.alert_type == "drought"]
        assert len(drought_alerts) == 1
        assert drought_alerts[0].severity == "severe_warning"

    def test_no_drought_alert_below_threshold(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"rainfall_deficit_pct": 10.0, "temperature_c": 27.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        assert not any(a.alert_type == "drought" for a in alerts)

    def test_heatwave_warning_at_40c(
        self, alert_gen: AlertGenerator, northwest_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"temperature_c": 40.0, "rainfall_mm": 0.0}
        alerts = alert_gen.evaluate_conditions(northwest_india, data)
        heat_alerts = [a for a in alerts if a.alert_type == "heatwave"]
        assert len(heat_alerts) == 1
        assert heat_alerts[0].severity == "warning"

    def test_severe_heatwave_at_45c(
        self, alert_gen: AlertGenerator, northwest_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"temperature_c": 45.0, "rainfall_mm": 0.0}
        alerts = alert_gen.evaluate_conditions(northwest_india, data)
        heat_alerts = [a for a in alerts if a.alert_type == "heatwave"]
        assert len(heat_alerts) == 1
        assert heat_alerts[0].severity == "severe_warning"

    def test_no_heatwave_below_threshold(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"temperature_c": 35.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        assert not any(a.alert_type == "heatwave" for a in alerts)

    def test_cold_wave_at_5c(
        self, alert_gen: AlertGenerator, northwest_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"temperature_c": 5.0}
        alerts = alert_gen.evaluate_conditions(northwest_india, data)
        cold_alerts = [a for a in alerts if a.alert_type == "cold_wave"]
        assert len(cold_alerts) == 1
        assert cold_alerts[0].severity == "warning"

    def test_cold_wave_at_zero(
        self, alert_gen: AlertGenerator, northwest_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"temperature_c": 0.0}
        alerts = alert_gen.evaluate_conditions(northwest_india, data)
        assert any(a.alert_type == "cold_wave" for a in alerts)

    def test_no_cold_wave_above_threshold(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"temperature_c": 10.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        assert not any(a.alert_type == "cold_wave" for a in alerts)

    def test_cyclone_watch_at_64kmh(
        self, alert_gen: AlertGenerator, southern_peninsula: ClimateZone
    ) -> None:
        data: dict[str, object] = {"wind_kmh": 64.0, "temperature_c": 28.0}
        alerts = alert_gen.evaluate_conditions(southern_peninsula, data)
        cyclone_alerts = [a for a in alerts if a.alert_type == "cyclone"]
        assert len(cyclone_alerts) == 1
        assert cyclone_alerts[0].severity == "warning"

    def test_severe_cyclone_at_118kmh(
        self, alert_gen: AlertGenerator, southern_peninsula: ClimateZone
    ) -> None:
        data: dict[str, object] = {"wind_kmh": 118.0, "temperature_c": 28.0}
        alerts = alert_gen.evaluate_conditions(southern_peninsula, data)
        cyclone_alerts = [a for a in alerts if a.alert_type == "cyclone"]
        assert len(cyclone_alerts) == 1
        assert cyclone_alerts[0].severity == "severe_warning"

    def test_no_cyclone_below_threshold(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"wind_kmh": 30.0, "temperature_c": 27.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        assert not any(a.alert_type == "cyclone" for a in alerts)

    def test_multiple_simultaneous_alerts(
        self, alert_gen: AlertGenerator, southern_peninsula: ClimateZone
    ) -> None:
        """High rainfall + drought deficit + high wind can all trigger simultaneously."""
        data: dict[str, object] = {
            "rainfall_mm": 250.0,
            "temperature_c": 42.0,
            "wind_kmh": 70.0,
            "rainfall_deficit_pct": 0.0,
        }
        alerts = alert_gen.evaluate_conditions(southern_peninsula, data)
        # Should get flood + heatwave + cyclone
        types = {a.alert_type for a in alerts}
        assert "flood" in types
        assert "heatwave" in types
        assert "cyclone" in types

    def test_alert_has_valid_uuid(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"rainfall_mm": 250.0, "temperature_c": 27.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        assert len(alerts) > 0
        import uuid
        uuid.UUID(alerts[0].alert_id)  # should not raise

    def test_alert_valid_until_after_issued_at(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"rainfall_mm": 250.0, "temperature_c": 27.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        for alert in alerts:
            assert alert.valid_until > alert.issued_at

    def test_alert_message_contains_zone_name(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"rainfall_mm": 250.0, "temperature_c": 27.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        for alert in alerts:
            assert "Central India" in alert.message

    def test_alert_affected_zones_contains_zone_id(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"rainfall_mm": 250.0, "temperature_c": 27.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        for alert in alerts:
            assert "central-india" in alert.affected_zones

    def test_evaluate_conditions_returns_list(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        alerts = alert_gen.evaluate_conditions(central_india, {})
        assert isinstance(alerts, list)

    def test_evaluate_empty_data_uses_zone_defaults(
        self, alert_gen: AlertGenerator, northwest_india: ClimateZone
    ) -> None:
        alerts = alert_gen.evaluate_conditions(northwest_india, {})
        # Empty data should use zone avg_temp_c (24°C), no flood, no extreme events
        assert isinstance(alerts, list)

    def test_issued_at_is_utc_aware(
        self, alert_gen: AlertGenerator, central_india: ClimateZone
    ) -> None:
        data: dict[str, object] = {"rainfall_mm": 300.0}
        alerts = alert_gen.evaluate_conditions(central_india, data)
        for alert in alerts:
            assert alert.issued_at.tzinfo is not None


# ---------------------------------------------------------------------------
# ClimateAnalyzer tests
# ---------------------------------------------------------------------------


class TestClimateAnalyzer:
    def test_generate_report_returns_climate_report(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
        normal_conditions: dict[str, object],
    ) -> None:
        report = analyzer.generate_report(central_india, normal_conditions)
        assert isinstance(report, ClimateReport)

    def test_report_zone_matches_input(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
        normal_conditions: dict[str, object],
    ) -> None:
        report = analyzer.generate_report(central_india, normal_conditions)
        assert report.zone.zone_id == "central-india"

    def test_report_current_conditions_matches_input(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
        normal_conditions: dict[str, object],
    ) -> None:
        report = analyzer.generate_report(central_india, normal_conditions)
        assert report.current_conditions == normal_conditions

    def test_report_has_forecast(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
        normal_conditions: dict[str, object],
    ) -> None:
        report = analyzer.generate_report(central_india, normal_conditions)
        assert len(report.forecast) > 0

    def test_report_forecast_contains_next_24h(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
        normal_conditions: dict[str, object],
    ) -> None:
        report = analyzer.generate_report(central_india, normal_conditions)
        assert "next_24h" in report.forecast

    def test_report_forecast_contains_next_7_days(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
        normal_conditions: dict[str, object],
    ) -> None:
        report = analyzer.generate_report(central_india, normal_conditions)
        assert "next_7_days" in report.forecast

    def test_report_alerts_is_list(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
        normal_conditions: dict[str, object],
    ) -> None:
        report = analyzer.generate_report(central_india, normal_conditions)
        assert isinstance(report.alerts, list)

    def test_report_extreme_conditions_generate_alerts(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
    ) -> None:
        extreme_data: dict[str, object] = {
            "temperature_c": 46.0,
            "rainfall_mm": 500.0,
            "humidity_pct": 95.0,
            "wind_kmh": 50.0,
            "rainfall_deficit_pct": 0.0,
        }
        report = analyzer.generate_report(central_india, extreme_data)
        assert len(report.alerts) > 0

    def test_report_wetter_than_normal_trend(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
    ) -> None:
        # rainfall_mm > avg_rainfall_mm / 30 means "wetter than normal"
        wet_data: dict[str, object] = {
            "temperature_c": 27.0,
            "rainfall_mm": central_india.avg_rainfall_mm / 30 + 10.0,
            "humidity_pct": 80.0,
        }
        report = analyzer.generate_report(central_india, wet_data)
        next_7 = report.forecast.get("next_7_days", {})
        assert isinstance(next_7, dict)
        assert next_7.get("trend") == "wetter than normal"

    def test_report_drier_than_normal_trend(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
    ) -> None:
        # rainfall_mm < avg_rainfall_mm / 60 means "drier than normal"
        dry_data: dict[str, object] = {
            "temperature_c": 27.0,
            "rainfall_mm": 0.1,
            "humidity_pct": 30.0,
        }
        report = analyzer.generate_report(central_india, dry_data)
        next_7 = report.forecast.get("next_7_days", {})
        assert isinstance(next_7, dict)
        assert next_7.get("trend") == "drier than normal"

    def test_report_temperature_above_normal(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
    ) -> None:
        hot_data: dict[str, object] = {
            "temperature_c": central_india.avg_temp_c + 5.0,
            "rainfall_mm": 10.0,
        }
        report = analyzer.generate_report(central_india, hot_data)
        next_7 = report.forecast.get("next_7_days", {})
        assert isinstance(next_7, dict)
        assert next_7.get("temperature_trend") == "above normal"

    def test_report_temperature_below_normal(
        self,
        analyzer: ClimateAnalyzer,
        central_india: ClimateZone,
    ) -> None:
        cold_data: dict[str, object] = {
            "temperature_c": central_india.avg_temp_c - 5.0,
            "rainfall_mm": 10.0,
        }
        report = analyzer.generate_report(central_india, cold_data)
        next_7 = report.forecast.get("next_7_days", {})
        assert isinstance(next_7, dict)
        assert next_7.get("temperature_trend") == "below normal"

    def test_trend_analysis_empty_returns_error(
        self, analyzer: ClimateAnalyzer, central_india: ClimateZone
    ) -> None:
        result = analyzer.trend_analysis(central_india, [])
        assert "error" in result

    def test_trend_analysis_returns_zone_info(
        self, analyzer: ClimateAnalyzer, central_india: ClimateZone
    ) -> None:
        historical = [
            {"temperature_c": 28.0, "rainfall_mm": 30.0},
            {"temperature_c": 30.0, "rainfall_mm": 25.0},
            {"temperature_c": 26.0, "rainfall_mm": 35.0},
        ]
        result = analyzer.trend_analysis(central_india, historical)
        assert result["zone_id"] == "central-india"
        assert result["zone_name"] == "Central India"
        assert result["observations"] == 3

    def test_trend_analysis_temperature_stats(
        self, analyzer: ClimateAnalyzer, central_india: ClimateZone
    ) -> None:
        historical = [
            {"temperature_c": 28.0, "rainfall_mm": 10.0},
            {"temperature_c": 32.0, "rainfall_mm": 10.0},
            {"temperature_c": 24.0, "rainfall_mm": 10.0},
        ]
        result = analyzer.trend_analysis(central_india, historical)
        temp = result["temperature"]
        assert isinstance(temp, dict)
        assert temp["mean_c"] == pytest.approx(28.0, abs=0.01)
        assert temp["min_c"] == 24.0
        assert temp["max_c"] == 32.0

    def test_trend_analysis_rainfall_stats(
        self, analyzer: ClimateAnalyzer, central_india: ClimateZone
    ) -> None:
        historical = [
            {"temperature_c": 27.0, "rainfall_mm": 10.0},
            {"temperature_c": 27.0, "rainfall_mm": 20.0},
            {"temperature_c": 27.0, "rainfall_mm": 30.0},
        ]
        result = analyzer.trend_analysis(central_india, historical)
        rain = result["rainfall"]
        assert isinstance(rain, dict)
        assert rain["total_mm"] == pytest.approx(60.0, abs=0.01)
        assert rain["mean_daily_mm"] == pytest.approx(20.0, abs=0.01)

    def test_trend_analysis_anomaly_calculation(
        self, analyzer: ClimateAnalyzer, central_india: ClimateZone
    ) -> None:
        # avg_temp_c for central-india is 27.0
        historical = [{"temperature_c": 30.0, "rainfall_mm": 0.0}]
        result = analyzer.trend_analysis(central_india, historical)
        temp = result["temperature"]
        assert isinstance(temp, dict)
        assert temp["anomaly_vs_normal_c"] == pytest.approx(3.0, abs=0.01)

    def test_trend_analysis_no_temp_data(
        self, analyzer: ClimateAnalyzer, central_india: ClimateZone
    ) -> None:
        historical = [{"rainfall_mm": 10.0}, {"rainfall_mm": 20.0}]
        result = analyzer.trend_analysis(central_india, historical)
        assert "temperature" not in result
        assert "rainfall" in result

    def test_trend_analysis_no_rainfall_data(
        self, analyzer: ClimateAnalyzer, central_india: ClimateZone
    ) -> None:
        historical = [{"temperature_c": 25.0}, {"temperature_c": 27.0}]
        result = analyzer.trend_analysis(central_india, historical)
        assert "rainfall" not in result
        assert "temperature" in result

    def test_trend_analysis_single_observation(
        self, analyzer: ClimateAnalyzer, central_india: ClimateZone
    ) -> None:
        historical = [{"temperature_c": 27.0, "rainfall_mm": 50.0}]
        result = analyzer.trend_analysis(central_india, historical)
        assert result["observations"] == 1
        assert "temperature" in result
        assert "rainfall" in result


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


@given(
    rainfall_mm=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    temperature_c=st.floats(min_value=-20.0, max_value=55.0, allow_nan=False, allow_infinity=False),
    wind_kmh=st.floats(min_value=0.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    deficit_pct=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=30)
def test_alert_generator_never_raises(
    rainfall_mm: float,
    temperature_c: float,
    wind_kmh: float,
    deficit_pct: float,
) -> None:
    """evaluate_conditions must never raise for any numeric input combination."""
    registry = ClimateZoneRegistry()
    zone = registry.get_zone("central-india")
    assert zone is not None
    gen = AlertGenerator()
    data: dict[str, object] = {
        "rainfall_mm": rainfall_mm,
        "temperature_c": temperature_c,
        "wind_kmh": wind_kmh,
        "rainfall_deficit_pct": deficit_pct,
    }
    alerts = gen.evaluate_conditions(zone, data)
    assert isinstance(alerts, list)
    for alert in alerts:
        assert isinstance(alert, WeatherAlert)


@given(
    n=st.integers(min_value=1, max_value=30),
    base_temp=st.floats(min_value=10.0, max_value=35.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20)
def test_trend_analysis_observation_count(n: int, base_temp: float) -> None:
    """trend_analysis observation count matches input length."""
    registry = ClimateZoneRegistry()
    zone = registry.get_zone("central-india")
    assert zone is not None
    analyzer = ClimateAnalyzer()
    historical = [{"temperature_c": base_temp, "rainfall_mm": 10.0} for _ in range(n)]
    result = analyzer.trend_analysis(zone, historical)
    assert result["observations"] == n


@given(zone_id=st.sampled_from([
    "northwest-india",
    "northeast-india",
    "central-india",
    "western-india",
    "southern-peninsula",
    "eastern-india",
]))
@settings(max_examples=10)
def test_all_zone_ids_resolvable(zone_id: str) -> None:
    registry = ClimateZoneRegistry()
    zone = registry.get_zone(zone_id)
    assert zone is not None
    assert zone.zone_id == zone_id
