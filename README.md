# Warsaw to Hel good weather forecast for kitesurfing trip alert

As a kitesurfer living in Warsaw (Poland), I wanted to build an alert for good weather conditions on the Hel Peninsula. Using this program you get alerted via email for good weather forecast conditions so you can pack your equipment and drive ~5h for at least 2 days of flying on the Puck Bay.

## Features

- **7-Day Wind Forecast**: Fetches hourly-resolution wind forecast from Open-Meteo API (no API key required)
- **Smart Detection**: Analyzes forecasted wind to find consecutive days meeting your criteria
- **Email Alerts**: Notifies you of good forecast days so you can plan your trip

## Files

- `alert/check_forecast.py` — main script that fetches forecast, analyzes it and sends an email alert.
- `alert/requirements.txt` — Python dependencies.
- `.env.example` — example configuration including SMTP settings.

## Quick start

1. Copy `.env.example` to `.env` and fill SMTP credentials and `EMAIL_TO`.

2. Install dependencies:

```bash
python3 -m pip install -r alert/requirements.txt
```

3. Run a dry run to see a summary (no email sent):

```bash
python3 alert/check_forecast.py --dry-run
```

4. To actually send alerts, run the script without `--dry-run` (ensure `.env` is loaded into the environment, e.g. use `export $(cat .env | xargs)` or a process manager that loads the file).

### Cron example

Run daily at 08:00 and log output:

```cron
0 8 * * * cd /path/to/repo && /usr/bin/env python3 alert/check_forecast.py >> /path/to/repo/alert/log.txt 2>&1
```

## Configuration

Edit `.env` to customize alert criteria:

- `LAT`, `LON` — forecast location (default: Hel Peninsula, 54.6806°N, 18.5591°E)
- `MIN_WIND_KNOTS`, `MAX_WIND_KNOTS` — wind range for "good" conditions (knots)
- `MIN_HOURS_PER_DAY` — minimum hours per day within wind range
- `REQUIRED_CONSECUTIVE_DAYS` — consecutive days needed to trigger alert
- `FORECAST_DAYS` — how far ahead to forecast (default: 7 days)

## Notes

- **Forecast-based** (not real-time): Predicts good conditions up to 7 days in advance so you can plan your trip
- Uses Open-Meteo's free, reliable forecast API with hourly resolution
- Timezone: `Europe/Warsaw`
