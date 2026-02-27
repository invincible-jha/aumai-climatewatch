"""
aumai-climatewatch quickstart examples.

Run this file directly to verify your installation and explore the API:

    python examples/quickstart.py

Each demo function is self-contained and prints clearly labelled output.
"""

from __future__ import annotations

from aumai_climatewatch.core import AlertGenerator, ClimateAnalyzer, ClimateZoneRegistry


# ---------------------------------------------------------------------------
# Demo 1: Browse climate zones
# ---------------------------------------------------------------------------


def demo_climate_zones() -> None:
    """List all India climate zones with state membership and climate normals."""
    print("\n" + "=" * 60)
    print("DEMO 1: India Climate Zone Registry")
    print("=" * 60)

    registry = ClimateZoneRegistry()
    all_zones = registry.all_zones()

    print(f"\nTotal climate zones: {len(all_zones)}")
    print(f"\n{'Zone ID':<24} {'Name':<24} {'Rain(mm)':>9} {'Temp(C)':>8} {'States':>6}")
    print("-" * 78)
    for zone in all_zones:
        print(f"{zone.zone_id:<24} {zone.name:<24} "
              f"{zone.avg_rainfall_mm:>9.0f} {zone.avg_temp_c:>8.1f} "
              f"{len(zone.states):>6}")
        print(f"  States: {', '.join(zone.states[:4])}"
              + (f" +{len(zone.states)-4} more" if len(zone.states) > 4 else ""))

    # Lookup by state
    print("\nState lookups:")
    for state in ("Maharashtra", "Bihar", "Rajasthan", "Kerala", "Assam"):
        zones = registry.zones_for_state(state)
        if zones:
            print(f"  {state:<20} -> {zones[0].name} ({zones[0].zone_id})")
        else:
            print(f"  {state:<20} -> not found")


# ---------------------------------------------------------------------------
# Demo 2: Alert generation — multiple event types
# ---------------------------------------------------------------------------


def demo_alert_generation() -> None:
    """Generate weather alerts for different extreme event scenarios across India."""
    print("\n" + "=" * 60)
    print("DEMO 2: Alert Generation — Extreme Event Scenarios")
    print("=" * 60)

    registry = ClimateZoneRegistry()
    generator = AlertGenerator()

    scenarios = [
        {
            "description": "Bihar — Peak monsoon flood risk",
            "zone_id": "eastern-india",
            "obs": {
                "temperature_c": 32.0,
                "rainfall_mm": 350.0,   # severe flood: > 400 mm is severe, > 200 mm is warning
                "humidity_pct": 92.0,
                "wind_kmh": 25.0,
                "rainfall_deficit_pct": 0.0,
            },
        },
        {
            "description": "Rajasthan — Summer heatwave + severe drought",
            "zone_id": "northwest-india",
            "obs": {
                "temperature_c": 47.5,  # severe heatwave: > 45°C
                "rainfall_mm": 1.0,
                "humidity_pct": 12.0,
                "wind_kmh": 30.0,
                "rainfall_deficit_pct": 58.0,   # severe drought: > 50%
            },
        },
        {
            "description": "Odisha coast — Cyclone approach",
            "zone_id": "central-india",
            "obs": {
                "temperature_c": 28.0,
                "rainfall_mm": 180.0,
                "humidity_pct": 88.0,
                "wind_kmh": 130.0,   # severe cyclone: > 118 km/h
                "rainfall_deficit_pct": 0.0,
            },
        },
        {
            "description": "North India — Winter cold wave",
            "zone_id": "eastern-india",
            "obs": {
                "temperature_c": 3.0,  # cold wave: <= 5°C
                "rainfall_mm": 5.0,
                "humidity_pct": 70.0,
                "wind_kmh": 15.0,
                "rainfall_deficit_pct": 0.0,
            },
        },
        {
            "description": "Southern Peninsula — Normal conditions",
            "zone_id": "southern-peninsula",
            "obs": {
                "temperature_c": 30.0,
                "rainfall_mm": 40.0,
                "humidity_pct": 65.0,
                "wind_kmh": 15.0,
                "rainfall_deficit_pct": 5.0,
            },
        },
    ]

    for scenario in scenarios:
        zone = registry.get_zone(scenario["zone_id"])
        if zone is None:
            continue
        alerts = generator.evaluate_conditions(zone, scenario["obs"])
        print(f"\nScenario: {scenario['description']}")
        print(f"  Zone: {zone.name} (avg temp: {zone.avg_temp_c}°C, "
              f"avg rain: {zone.avg_rainfall_mm:.0f} mm/yr)")
        if not alerts:
            print("  Status: No active alerts. Conditions within normal range.")
        else:
            print(f"  Alerts generated: {len(alerts)}")
            for alert in alerts:
                print(f"    [{alert.severity.upper()}] {alert.alert_type.upper()}")
                print(f"    {alert.message[:100]}...")
                print(f"    Alert ID: {alert.alert_id}")
                print(f"    Valid until: {alert.valid_until.strftime('%Y-%m-%d %H:%M UTC')}")


# ---------------------------------------------------------------------------
# Demo 3: Climate report generation
# ---------------------------------------------------------------------------


def demo_climate_report() -> None:
    """Generate a full climate report for Central India during a drought period."""
    print("\n" + "=" * 60)
    print("DEMO 3: Climate Report — Central India, Pre-Kharif Drought")
    print("=" * 60)

    registry = ClimateZoneRegistry()
    analyzer = ClimateAnalyzer()

    zone = registry.get_zone("central-india")
    if zone is None:
        print("ERROR: zone not found")
        return

    # Pre-kharif conditions with significant rainfall deficit
    observations = {
        "temperature_c": 43.5,
        "rainfall_mm": 4.0,
        "humidity_pct": 22.0,
        "wind_kmh": 18.0,
        "rainfall_deficit_pct": 38.0,  # drought watch: > 25%
    }

    report = analyzer.generate_report(zone, observations)

    print(f"\nZone: {report.zone.name}")
    print(f"States: {', '.join(report.zone.states)}")
    print(f"\nCurrent Conditions:")
    for key, value in report.current_conditions.items():
        print(f"  {key}: {value}")

    print(f"\nActive Alerts: {len(report.alerts)}")
    for alert in report.alerts:
        print(f"  [{alert.severity.upper()}] {alert.alert_type.upper()}")
        print(f"    {alert.message}")

    print("\nForecast:")
    next_24h = report.forecast.get("next_24h", {})
    print(f"  Next 24h:")
    print(f"    Temperature: {next_24h.get('temperature_c', 'N/A')}°C")
    print(f"    Expected rainfall: {next_24h.get('expected_rainfall_mm', 'N/A'):.1f} mm")
    print(f"    Advisory: {next_24h.get('advisory', 'N/A')}")

    next_7d = report.forecast.get("next_7_days", {})
    print(f"  Next 7 days:")
    print(f"    Rainfall trend: {next_7d.get('trend', 'N/A')}")
    print(f"    Temperature trend: {next_7d.get('temperature_trend', 'N/A')}")


# ---------------------------------------------------------------------------
# Demo 4: Trend analysis over historical observations
# ---------------------------------------------------------------------------


def demo_trend_analysis() -> None:
    """Analyse a 90-day temperature and rainfall trend for Northwest India."""
    print("\n" + "=" * 60)
    print("DEMO 4: Trend Analysis — Northwest India, 90-Day Summer Period")
    print("=" * 60)

    registry = ClimateZoneRegistry()
    analyzer = ClimateAnalyzer()

    zone = registry.get_zone("northwest-india")
    if zone is None:
        print("ERROR: zone not found")
        return

    print(f"\nZone normals — {zone.name}:")
    print(f"  Average annual temperature: {zone.avg_temp_c}°C")
    print(f"  Average annual rainfall: {zone.avg_rainfall_mm:.0f} mm")

    # Simulate 90 days of above-normal summer temperatures with sparse rainfall
    # Day pattern: temperature oscillates 38-46°C; rain only on 6 days out of 90
    historical: list[dict[str, object]] = []
    for day in range(90):
        temp = 38.0 + (day % 9)  # oscillates 38 to 46°C
        rain = 8.0 if day % 15 == 0 else 0.5   # sparse rain events
        historical.append({"temperature_c": temp, "rainfall_mm": rain})

    trend = analyzer.trend_analysis(zone, historical)

    print(f"\nTrend analysis over {trend['observations']} days:")

    temp_stats = trend.get("temperature", {})
    print(f"\nTemperature:")
    print(f"  Mean: {temp_stats.get('mean_c', 'N/A')}°C")
    print(f"  Min:  {temp_stats.get('min_c', 'N/A')}°C")
    print(f"  Max:  {temp_stats.get('max_c', 'N/A')}°C")
    anomaly = temp_stats.get("anomaly_vs_normal_c", 0)
    print(f"  Anomaly vs normal: {anomaly:+.2f}°C "
          f"({'ABOVE' if anomaly > 0 else 'BELOW'} normal)")

    rain_stats = trend.get("rainfall", {})
    print(f"\nRainfall:")
    print(f"  Total (90 days): {rain_stats.get('total_mm', 'N/A'):.1f} mm")
    print(f"  Mean daily:      {rain_stats.get('mean_daily_mm', 'N/A'):.2f} mm/day")
    deficit = rain_stats.get("deficit_vs_normal_pct", 0)
    print(f"  Deficit vs normal: {deficit:.1f}%")

    # Classify severity
    if deficit >= 50:
        status = "SEVERE DROUGHT"
    elif deficit >= 25:
        status = "DROUGHT WATCH"
    elif deficit <= -20:
        status = "ABOVE NORMAL RAINFALL"
    else:
        status = "NEAR NORMAL"
    print(f"\n  Rainfall status: {status}")


# ---------------------------------------------------------------------------
# Demo 5: Multi-zone monitoring sweep
# ---------------------------------------------------------------------------


def demo_multi_zone_sweep() -> None:
    """Simulate a monitoring dashboard sweep across all six Indian climate zones."""
    print("\n" + "=" * 60)
    print("DEMO 5: Multi-Zone Monitoring Dashboard Sweep")
    print("=" * 60)

    registry = ClimateZoneRegistry()
    generator = AlertGenerator()

    # Representative summer observations — zone-specific
    zone_obs: dict[str, dict[str, object]] = {
        "northwest-india":     {"temperature_c": 46.0, "rainfall_mm": 2.0,
                                "humidity_pct": 15.0, "wind_kmh": 28.0,
                                "rainfall_deficit_pct": 52.0},
        "northeast-india":     {"temperature_c": 28.0, "rainfall_mm": 220.0,
                                "humidity_pct": 90.0, "wind_kmh": 20.0,
                                "rainfall_deficit_pct": 0.0},
        "central-india":       {"temperature_c": 43.0, "rainfall_mm": 3.0,
                                "humidity_pct": 25.0, "wind_kmh": 20.0,
                                "rainfall_deficit_pct": 30.0},
        "western-india":       {"temperature_c": 39.0, "rainfall_mm": 10.0,
                                "humidity_pct": 48.0, "wind_kmh": 22.0,
                                "rainfall_deficit_pct": 8.0},
        "southern-peninsula":  {"temperature_c": 35.0, "rainfall_mm": 55.0,
                                "humidity_pct": 72.0, "wind_kmh": 18.0,
                                "rainfall_deficit_pct": 0.0},
        "eastern-india":       {"temperature_c": 36.0, "rainfall_mm": 25.0,
                                "humidity_pct": 68.0, "wind_kmh": 14.0,
                                "rainfall_deficit_pct": 12.0},
    }

    print("\nINDIA CLIMATE ALERT DASHBOARD")
    print(f"{'Zone':<26} {'Temp(C)':>8} {'Rain(mm)':>10} {'Alerts':>8}")
    print("-" * 60)

    total_alerts = 0
    for zone_id, obs in zone_obs.items():
        zone = registry.get_zone(zone_id)
        if zone is None:
            continue
        alerts = generator.evaluate_conditions(zone, obs)
        total_alerts += len(alerts)
        temp = obs["temperature_c"]
        rain = obs["rainfall_mm"]
        alert_str = (f"{len(alerts)} ({', '.join(a.alert_type for a in alerts)})"
                     if alerts else "None")
        print(f"{zone.name:<26} {temp:>8.1f} {rain:>10.1f} {alert_str:>8}")

    print("-" * 60)
    print(f"Total active alerts: {total_alerts}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run all ClimateWatch quickstart demos in sequence."""
    print("aumai-climatewatch — Quickstart Demo")
    print("Climate monitoring and early warning for India")

    demo_climate_zones()
    demo_alert_generation()
    demo_climate_report()
    demo_trend_analysis()
    demo_multi_zone_sweep()

    print("\n" + "=" * 60)
    print("All demos complete.")
    print("\nDISCLAIMER: Climate and weather data are estimates based on historical averages")
    print("and modelled projections. Do not use as the sole basis for emergency response.")
    print("Always verify with IMD (mausam.imd.gov.in) before taking action.")
    print("=" * 60)


if __name__ == "__main__":
    main()
