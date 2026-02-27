"""CLI entry point for aumai-climatewatch."""

from __future__ import annotations

import json
import sys

import click

from .core import AlertGenerator, ClimateAnalyzer, ClimateZoneRegistry
from .models import ENVIRONMENTAL_DISCLAIMER


@click.group()
@click.version_option()
def main() -> None:
    """AumAI ClimateWatch — Climate monitoring and early warning for India."""


@main.command("alerts")
@click.option("--zone", required=True, help="Zone ID (e.g. central-india, western-india)")
@click.option("--data", "data_file", type=click.Path(exists=True), default=None, help="JSON file with current weather observations")
def alerts(zone: str, data_file: str | None) -> None:
    """Generate weather alerts for a climate zone."""
    registry = ClimateZoneRegistry()
    zone_obj = registry.get_zone(zone)
    if zone_obj is None:
        available = [z.zone_id for z in registry.all_zones()]
        click.echo(f"Error: Zone '{zone}' not found. Available zones: {', '.join(available)}", err=True)
        sys.exit(1)

    if data_file:
        with open(data_file) as fh:
            weather_data: dict[str, object] = json.load(fh)
    else:
        # Use sample data at zone average + slight perturbations for demonstration
        weather_data = {
            "temperature_c": zone_obj.avg_temp_c + 2.0,
            "rainfall_mm": zone_obj.avg_rainfall_mm / 30,
            "humidity_pct": 65.0,
            "wind_kmh": 15.0,
            "rainfall_deficit_pct": 10.0,
        }

    generator = AlertGenerator()
    alert_list = generator.evaluate_conditions(zone_obj, weather_data)

    click.echo(f"\nWEATHER ALERTS: {zone_obj.name}")
    click.echo(f"States: {', '.join(zone_obj.states)}")
    click.echo("=" * 60)

    if not alert_list:
        click.echo("No active alerts. Conditions are within normal range.")
    else:
        for alert in alert_list:
            click.echo(f"\nALERT TYPE: {alert.alert_type.upper()}")
            click.echo(f"SEVERITY:   {alert.severity.upper()}")
            click.echo(f"MESSAGE:    {alert.message}")
            click.echo(f"VALID UNTIL: {alert.valid_until.strftime('%Y-%m-%d %H:%M UTC')}")

    click.echo(f"\nDISCLAIMER: {ENVIRONMENTAL_DISCLAIMER}\n")


@main.command("report")
@click.option("--zone", required=True, help="Zone ID (e.g. central-india, western-india)")
@click.option("--data", "data_file", type=click.Path(exists=True), default=None, help="Optional JSON file with weather observations")
def report(zone: str, data_file: str | None) -> None:
    """Generate a full climate report for a zone."""
    registry = ClimateZoneRegistry()
    zone_obj = registry.get_zone(zone)
    if zone_obj is None:
        available = [z.zone_id for z in registry.all_zones()]
        click.echo(f"Error: Zone '{zone}' not found. Available: {', '.join(available)}", err=True)
        sys.exit(1)

    if data_file:
        with open(data_file) as fh:
            weather_data: dict[str, object] = json.load(fh)
    else:
        weather_data = {
            "temperature_c": zone_obj.avg_temp_c,
            "rainfall_mm": zone_obj.avg_rainfall_mm / 30,
            "humidity_pct": 65.0,
            "wind_kmh": 12.0,
            "rainfall_deficit_pct": 5.0,
        }

    analyzer = ClimateAnalyzer()
    climate_report = analyzer.generate_report(zone_obj, weather_data)

    click.echo(f"\nCLIMATE REPORT: {climate_report.zone.name}")
    click.echo("=" * 60)
    click.echo("\nCURRENT CONDITIONS:")
    for key, value in climate_report.current_conditions.items():
        click.echo(f"  {key}: {value}")

    click.echo(f"\nACTIVE ALERTS: {len(climate_report.alerts)}")
    for alert in climate_report.alerts:
        click.echo(f"  [{alert.severity.upper()}] {alert.alert_type}: {alert.message[:100]}...")

    click.echo("\nFORECAST:")
    for period, details in climate_report.forecast.items():
        click.echo(f"  {period}:")
        if isinstance(details, dict):
            for k, v in details.items():
                click.echo(f"    {k}: {v}")
    click.echo(f"\nDISCLAIMER: {ENVIRONMENTAL_DISCLAIMER}\n")


@main.command("zones")
def zones() -> None:
    """List all available climate zones."""
    registry = ClimateZoneRegistry()
    click.echo("\nINDIA CLIMATE ZONES:")
    click.echo(f"{'Zone ID':<22} {'Name':<22} {'Avg Rain (mm)':>14} {'Avg Temp (C)':>12}")
    click.echo("-" * 75)
    for zone in registry.all_zones():
        click.echo(f"{zone.zone_id:<22} {zone.name:<22} {zone.avg_rainfall_mm:>14.0f} {zone.avg_temp_c:>12.1f}")
    click.echo(f"\nDISCLAIMER: {ENVIRONMENTAL_DISCLAIMER}\n")


@main.command("serve")
@click.option("--port", default=8000, help="Port to serve on")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
def serve(port: int, host: str) -> None:
    """Start the ClimateWatch API server (not yet implemented)."""
    click.echo("Error: The ClimateWatch API server is not yet available. The api module has not been implemented.", err=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
