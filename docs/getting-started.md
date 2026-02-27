# Getting Started with aumai-climatewatch

This guide walks you from installation to generating your first climate alerts and reports for
an Indian climate zone in under ten minutes.

---

## Prerequisites

- **Python 3.11 or newer.** Check your version with `python --version`.
- **pip** or **uv** package manager.
- (Optional) A JSON file with current weather observations to use in place of the synthetic
  demo data.

No API keys, no database setup, no external services required. ClimateWatch runs entirely
in-process against its static zone registry.

---

## Installation

### With pip

```bash
pip install aumai-climatewatch
```

### With uv (recommended)

```bash
uv add aumai-climatewatch
```

### For development (editable install from source)

```bash
git clone https://github.com/aumai/aumai-climatewatch.git
cd aumai-climatewatch
pip install -e ".[dev]"
```

### Verify the installation

```bash
climatewatch --version
climatewatch --help
```

You should see the version number and subcommands: `alerts`, `report`, `zones`, `serve`.

---

## Step-by-Step Tutorial

### Step 1 — Explore India's climate zones

ClimateWatch divides India into six major climate zones aligned with IMD's meteorological
subdivision framework. Start by listing them:

```bash
climatewatch zones
```

From Python:

```python
from aumai_climatewatch.core import ClimateZoneRegistry

registry = ClimateZoneRegistry()

print(f"Total zones: {len(registry.all_zones())}")
for zone in registry.all_zones():
    print(f"\n{zone.zone_id}")
    print(f"  Name: {zone.name}")
    print(f"  States: {', '.join(zone.states)}")
    print(f"  Avg rainfall: {zone.avg_rainfall_mm:.0f} mm/year")
    print(f"  Avg temp: {zone.avg_temp_c}°C")
```

### Step 2 — Look up a zone by state name

If you know the state but not the zone ID, use `zones_for_state()`:

```python
from aumai_climatewatch.core import ClimateZoneRegistry

registry = ClimateZoneRegistry()

# Single state lookup
zones = registry.zones_for_state("Rajasthan")
print(f"Rajasthan is in: {zones[0].name} ({zones[0].zone_id})")

zones = registry.zones_for_state("Tamil Nadu")
print(f"Tamil Nadu is in: {zones[0].name}")

zones = registry.zones_for_state("Assam")
print(f"Assam is in: {zones[0].name}")
```

### Step 3 — Generate weather alerts

Pass a zone and a dictionary of current weather observations to `AlertGenerator`:

```python
from aumai_climatewatch.core import ClimateZoneRegistry, AlertGenerator

registry = ClimateZoneRegistry()
generator = AlertGenerator()

zone = registry.get_zone("eastern-india")

# Simulate heavy monsoon rainfall in Bihar
observations = {
    "temperature_c": 32.0,
    "rainfall_mm": 280.0,      # > 200 mm triggers flood warning
    "humidity_pct": 90.0,
    "wind_kmh": 25.0,
    "rainfall_deficit_pct": 0.0,
}

alerts = generator.evaluate_conditions(zone, observations)

if not alerts:
    print("No active alerts.")
else:
    for alert in alerts:
        print(f"[{alert.severity.upper()}] {alert.alert_type.upper()}")
        print(f"  {alert.message}")
        print(f"  Valid until: {alert.valid_until}")
```

### Step 4 — Generate a full climate report

A `ClimateReport` combines alerts with a short-range forecast summary:

```python
from aumai_climatewatch.core import ClimateZoneRegistry, ClimateAnalyzer

registry = ClimateZoneRegistry()
analyzer = ClimateAnalyzer()

zone = registry.get_zone("central-india")
observations = {
    "temperature_c": 44.0,    # heatwave territory
    "rainfall_mm": 3.0,
    "humidity_pct": 25.0,
    "wind_kmh": 20.0,
    "rainfall_deficit_pct": 30.0,  # drought watch
}

report = analyzer.generate_report(zone, observations)

print(f"Zone: {report.zone.name}")
print(f"Active alerts: {len(report.alerts)}")
for alert in report.alerts:
    print(f"  [{alert.severity}] {alert.alert_type}: {alert.message[:80]}...")

print(f"\n24h forecast: {report.forecast['next_24h']}")
print(f"7-day trend: {report.forecast['next_7_days']}")
```

### Step 5 — Use the CLI with observation data

Save observations to JSON and pass them via `--data`:

```bash
cat > bihar_monsoon.json << 'EOF'
{
  "temperature_c": 32.0,
  "rainfall_mm": 310.0,
  "humidity_pct": 92.0,
  "wind_kmh": 28.0,
  "rainfall_deficit_pct": 0.0
}
EOF

# Generate alerts
climatewatch alerts --zone eastern-india --data bihar_monsoon.json

# Generate full report
climatewatch report --zone eastern-india --data bihar_monsoon.json
```

### Step 6 — Run trend analysis on historical data

```python
from aumai_climatewatch.core import ClimateZoneRegistry, ClimateAnalyzer

registry = ClimateZoneRegistry()
analyzer = ClimateAnalyzer()
zone = registry.get_zone("northwest-india")

# Simulate 60 days of pre-monsoon observations in Rajasthan
historical = []
for day in range(60):
    historical.append({
        "temperature_c": 38.0 + (day % 8),   # oscillating high temperatures
        "rainfall_mm": 2.0 if day % 15 == 0 else 0.0,  # very sparse rainfall
    })

trend = analyzer.trend_analysis(zone, historical)

print(f"Zone: {trend['zone_name']}")
print(f"Observations: {trend['observations']}")
temp = trend["temperature"]
print(f"Mean temp: {temp['mean_c']}°C (anomaly: {temp['anomaly_vs_normal_c']:+.2f}°C vs normal)")
rain = trend["rainfall"]
print(f"Total rainfall: {rain['total_mm']} mm")
print(f"Deficit vs normal: {rain['deficit_vs_normal_pct']:.1f}%")
```

---

## Common Patterns and Recipes

### Recipe 1 — Alert monitoring loop for all zones

```python
from aumai_climatewatch.core import ClimateZoneRegistry, AlertGenerator

registry = ClimateZoneRegistry()
generator = AlertGenerator()

# Simulate a monitoring pass over all zones with representative summer observations
zone_observations = {
    "northwest-india":   {"temperature_c": 47.0, "rainfall_mm": 1.0, "humidity_pct": 15.0,
                          "wind_kmh": 25.0, "rainfall_deficit_pct": 55.0},
    "northeast-india":   {"temperature_c": 30.0, "rainfall_mm": 180.0, "humidity_pct": 88.0,
                          "wind_kmh": 20.0, "rainfall_deficit_pct": 0.0},
    "central-india":     {"temperature_c": 43.0, "rainfall_mm": 2.0, "humidity_pct": 22.0,
                          "wind_kmh": 18.0, "rainfall_deficit_pct": 30.0},
    "western-india":     {"temperature_c": 38.0, "rainfall_mm": 8.0, "humidity_pct": 45.0,
                          "wind_kmh": 22.0, "rainfall_deficit_pct": 5.0},
    "southern-peninsula":{"temperature_c": 34.0, "rainfall_mm": 60.0, "humidity_pct": 70.0,
                          "wind_kmh": 15.0, "rainfall_deficit_pct": 0.0},
    "eastern-india":     {"temperature_c": 36.0, "rainfall_mm": 15.0, "humidity_pct": 65.0,
                          "wind_kmh": 12.0, "rainfall_deficit_pct": 10.0},
}

print("INDIA CLIMATE ALERT SUMMARY")
print("=" * 60)
for zone_id, obs in zone_observations.items():
    zone = registry.get_zone(zone_id)
    alerts = generator.evaluate_conditions(zone, obs)
    status = "OK" if not alerts else f"{len(alerts)} ALERT(S)"
    print(f"{zone.name:<25} {status}")
    for alert in alerts:
        print(f"  [{alert.severity}] {alert.alert_type}")
```

### Recipe 2 — Serialize a report to JSON for a REST API response

```python
import json
from aumai_climatewatch.core import ClimateZoneRegistry, ClimateAnalyzer

registry = ClimateZoneRegistry()
analyzer = ClimateAnalyzer()

zone = registry.get_zone("southern-peninsula")
obs = {"temperature_c": 38.5, "rainfall_mm": 0.0, "humidity_pct": 45.0,
       "wind_kmh": 20.0, "rainfall_deficit_pct": 40.0}

report = analyzer.generate_report(zone, obs)

# Pydantic model_dump handles nested models; default=str handles datetime
payload = json.dumps(report.model_dump(), indent=2, default=str)
print(payload[:500], "...")
```

### Recipe 3 — Bridge ClimateWatch into a FarmBrain advisory

```python
from aumai_climatewatch.core import ClimateZoneRegistry, ClimateAnalyzer
from aumai_farmbrain.core import CropAdvisor, CropDatabase  # pip install aumai-farmbrain
from aumai_farmbrain.models import SoilProfile, WeatherData

# Climate input
registry = ClimateZoneRegistry()
analyzer = ClimateAnalyzer()
zone = registry.get_zone("eastern-india")
obs = {"temperature_c": 39.0, "rainfall_mm": 220.0, "humidity_pct": 88.0,
       "wind_kmh": 20.0, "rainfall_deficit_pct": 0.0}
report = analyzer.generate_report(zone, obs)

# Convert to FarmBrain WeatherData
weather = WeatherData(
    location=report.zone.name,
    temperature_c=float(report.current_conditions["temperature_c"]),
    humidity_pct=float(report.current_conditions["humidity_pct"]),
    rainfall_mm=float(report.current_conditions["rainfall_mm"]),
    forecast_days=7,
)

# Get crop advisory enriched with climate observations
db = CropDatabase()
soil = SoilProfile(ph=6.2, nitrogen_ppm=130.0, phosphorus_ppm=12.0,
                   potassium_ppm=150.0, organic_carbon_pct=0.7, soil_type="alluvial")
advisory = CropAdvisor().advise(db.by_name("rice"), soil, weather)

print(f"Risk alerts from climate integration: {len(advisory.risk_alerts)}")
for alert in advisory.risk_alerts:
    print(f"  {alert}")
```

### Recipe 4 — Construct and validate a WeatherAlert manually

```python
from aumai_climatewatch.models import WeatherAlert
from datetime import datetime, timezone, timedelta
import uuid

# Useful when consuming alerts from an external IMD API and mapping to ClimateWatch models
alert = WeatherAlert(
    alert_id=str(uuid.uuid4()),
    alert_type="cyclone",
    severity="severe_warning",
    affected_zones=["southern-peninsula"],
    message=(
        "SEVERE CYCLONE WARNING for Southern Peninsula. "
        "Cyclone Tej is expected to make landfall near Machilipatnam with winds of 140 km/h."
    ),
    issued_at=datetime.now(tz=timezone.utc),
    valid_until=datetime.now(tz=timezone.utc) + timedelta(hours=48),
)

print(f"Alert ID: {alert.alert_id}")
print(f"Type: {alert.alert_type}, Severity: {alert.severity}")
print(f"Zones: {alert.affected_zones}")
```

### Recipe 5 — Drought monitoring with cumulative rainfall data

```python
from aumai_climatewatch.core import ClimateZoneRegistry, ClimateAnalyzer, AlertGenerator

registry = ClimateZoneRegistry()
analyzer = ClimateAnalyzer()
generator = AlertGenerator()

zone = registry.get_zone("central-india")

# Simulate 90 days of below-normal rainfall (kharif season deficit)
historical = [{"temperature_c": 30.0, "rainfall_mm": 3.0} for _ in range(90)]
trend = analyzer.trend_analysis(zone, historical)

deficit = trend["rainfall"]["deficit_vs_normal_pct"]
print(f"Rainfall deficit over 90 days: {deficit:.1f}%")

# Generate a point-in-time alert with the deficit
obs = {
    "temperature_c": 32.0,
    "rainfall_mm": 2.0,
    "rainfall_deficit_pct": deficit,  # use computed deficit
    "humidity_pct": 40.0,
    "wind_kmh": 15.0,
}
alerts = generator.evaluate_conditions(zone, obs)
for alert in alerts:
    print(f"[{alert.severity}] {alert.alert_type}: {alert.message}")
```

---

## Troubleshooting FAQ

**Q: `climatewatch alerts` exits with "Zone 'X' not found".**

Run `climatewatch zones` to see the exact zone IDs. Use hyphens, not spaces or underscores:
`central-india`, not `central india` or `central_india`.

---

**Q: No alerts are generated even when I pass extreme values.**

Verify that the observation keys match exactly: `temperature_c`, `rainfall_mm`, `humidity_pct`,
`wind_kmh`, `rainfall_deficit_pct`. Missing keys are treated as zero or the zone average.
Check that numeric values are floats (or integers castable to float), not strings.

---

**Q: The forecast in the report looks unrealistically optimistic.**

The `next_24h` forecast uses an 80% dampening of current rainfall as a heuristic, and the
`next_7_days` trend is a simple comparison against zone annual averages. This is a
demonstration model — not a real numerical weather prediction. For production, replace the
forecast with data from the IMD API or a third-party weather service.

---

**Q: `trend_analysis()` returns `{"error": "No historical data provided."}`.**

Pass a non-empty list of observation dicts to `trend_analysis()`. Each dict should contain
at least `"temperature_c"` and/or `"rainfall_mm"` keys.

---

**Q: How do I add a new climate zone (e.g., Andaman and Nicobar)?**

Subclass `ClimateZoneRegistry` and add your zone in `__init__`:

```python
from aumai_climatewatch.core import ClimateZoneRegistry
from aumai_climatewatch.models import ClimateZone

class ExtendedRegistry(ClimateZoneRegistry):
    def __init__(self) -> None:
        super().__init__()
        andaman = ClimateZone(
            zone_id="andaman-nicobar",
            name="Andaman and Nicobar Islands",
            states=["Andaman and Nicobar Islands"],
            avg_rainfall_mm=3000.0,
            avg_temp_c=27.5,
        )
        self._zones[andaman.zone_id] = andaman
```

---

**Q: Alert IDs are different every time I run the same observation set.**

`alert_id` is a UUID4 generated at alert creation time. This is intentional — every alert
evaluation produces fresh, unique IDs for deduplication downstream. If you need stable IDs
for the same event, derive them from a hash of the zone ID, alert type, and `issued_at`
timestamp instead.

---

**Q: Can I use ClimateWatch with live IMD data?**

Yes. IMD publishes forecast data through its API at mausam.imd.gov.in. Fetch the relevant
observation or gridded forecast for your zone's geographic bounds, map the response fields
to the `dict[str, object]` format ClimateWatch expects
(`temperature_c`, `rainfall_mm`, `humidity_pct`, `wind_kmh`, `rainfall_deficit_pct`),
then call `AlertGenerator.evaluate_conditions()`.

---

## Next Steps

- Read the [API Reference](api-reference.md) for complete class and method documentation.
- Explore the [examples/quickstart.py](../examples/quickstart.py) for runnable demo code.
- See [CONTRIBUTING.md](../CONTRIBUTING.md) to add new zones or improve thresholds.
- For crop advisory integration, install [aumai-farmbrain](https://github.com/aumai/aumai-farmbrain).
- For farmer-facing alert delivery, see [aumai-kisanmitra](https://github.com/aumai/aumai-kisanmitra).
