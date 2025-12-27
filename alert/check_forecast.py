#!/usr/bin/env python3
"""Check wind forecast and send email alerts for good kitesurfing days."""
import os
import sys
import argparse
import datetime as dt
import requests
from email.message import EmailMessage
import smtplib


def load_env():
    cfg = {
        "LAT": float(os.getenv("LAT", "54.6806")),
        "LON": float(os.getenv("LON", "18.5591")),
        "MIN_WIND_KNOTS": float(os.getenv("MIN_WIND_KNOTS", "12")),
        "MAX_WIND_KNOTS": float(os.getenv("MAX_WIND_KNOTS", "30")),
        "MIN_HOURS_PER_DAY": int(os.getenv("MIN_HOURS_PER_DAY", "6")),
        "REQUIRED_CONSECUTIVE_DAYS": int(os.getenv("REQUIRED_CONSECUTIVE_DAYS", "2")),
        "FORECAST_DAYS": int(os.getenv("FORECAST_DAYS", "7")),
        "SMTP_HOST": os.getenv("SMTP_HOST"),
        "SMTP_PORT": int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None,
        "SMTP_USER": os.getenv("SMTP_USER"),
        "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
        "EMAIL_FROM": os.getenv("EMAIL_FROM"),
        "EMAIL_TO": os.getenv("EMAIL_TO"),
    }
    return cfg


def fetch_open_meteo(lat, lon, days):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&hourly=windspeed_10m"
        f"&timezone=Europe/Warsaw&forecast_days={days}"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


def mps_to_knots(mps):
    return mps * 1.94384449


def analyze_forecast(data, cfg):
    times = data.get("hourly", {}).get("time", [])
    speeds = data.get("hourly", {}).get("windspeed_10m", [])
    if not times or not speeds:
        raise ValueError("No hourly wind data available")

    # Map date -> hours meeting criteria
    day_hours = {}
    for t_iso, sp in zip(times, speeds):
        t = dt.datetime.fromisoformat(t_iso)
        date = t.date()
        kts = mps_to_knots(sp)
        ok = cfg["MIN_WIND_KNOTS"] <= kts <= cfg["MAX_WIND_KNOTS"]
        day_hours.setdefault(date, 0)
        if ok:
            day_hours[date] += 1

    # Build ordered list for next N days
    today = dt.date.today()
    ordered = []
    for i in range(cfg["FORECAST_DAYS"]):
        d = today + dt.timedelta(days=i)
        ordered.append((d, day_hours.get(d, 0)))

    # Find consecutive day runs
    runs = []
    current = []
    for d, hours in ordered:
        if hours >= cfg["MIN_HOURS_PER_DAY"]:
            current.append((d, hours))
        else:
            if current:
                runs.append(list(current))
                current = []
    if current:
        runs.append(list(current))

    # Check if any run meets required consecutive days
    good_runs = [r for r in runs if len(r) >= cfg["REQUIRED_CONSECUTIVE_DAYS"]]
    return ordered, runs, good_runs


def format_message(runs, ordered, cfg):
    lines = []
    lines.append("Good kitesurfing forecast detected on Hel Peninsula\n")
    lines.append("Forecast summary (date: good_hours):")
    for d, h in ordered:
        lines.append(f" - {d.isoformat()}: {h}h")
    lines.append("")
    lines.append(f"Thresholds: {cfg['MIN_WIND_KNOTS']}-{cfg['MAX_WIND_KNOTS']} knots, min {cfg['MIN_HOURS_PER_DAY']}h/day")
    lines.append("")
    lines.append("Matching runs:")
    for run in runs:
        if len(run) >= cfg["REQUIRED_CONSECUTIVE_DAYS"]:
            start = run[0][0].isoformat()
            end = run[-1][0].isoformat()
            lines.append(f" - {start} to {end} ({len(run)} days)")
    return "\n".join(lines)


def send_email(subject, body, cfg):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["EMAIL_FROM"]
    msg["To"] = cfg["EMAIL_TO"]
    msg.set_content(body)

    host = cfg["SMTP_HOST"]
    port = cfg["SMTP_PORT"] or 587
    user = cfg["SMTP_USER"]
    pwd = cfg["SMTP_PASSWORD"]
    if not host or not cfg["EMAIL_FROM"] or not cfg["EMAIL_TO"]:
        raise ValueError("SMTP_HOST, EMAIL_FROM and EMAIL_TO must be set in environment")

    with smtplib.SMTP(host, port, timeout=30) as s:
        # Only start TLS if the server advertises the STARTTLS extension.
        try:
            s.ehlo()
            if s.has_extn('starttls'):
                s.starttls()
                s.ehlo()
        except Exception:
            # If STARTTLS negotiation fails, fall back to plain connection.
            pass
        if user and pwd:
            s.login(user, pwd)
        s.send_message(msg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Don't send email, just print summary")
    args = parser.parse_args()

    cfg = load_env()
    try:
        data = fetch_open_meteo(cfg["LAT"], cfg["LON"], cfg["FORECAST_DAYS"])
    except Exception as e:
        print("Failed to fetch forecast:", e)
        sys.exit(2)

    ordered, runs, good_runs = analyze_forecast(data, cfg)

    if not good_runs:
        print("No suitable runs found. Summary:")
        for d, h in ordered:
            print(f"{d.isoformat()}: {h}h")
        return

    body = format_message(good_runs, ordered, cfg)
    subject = "Kitesurfing alert: good forecast on Hel Peninsula"
    if args.dry_run:
        print(subject)
        print(body)
        return

    try:
        send_email(subject, body, cfg)
        print("Alert email sent to", cfg["EMAIL_TO"])
    except Exception as e:
        print("Failed to send email:", e)
        sys.exit(3)


if __name__ == "__main__":
    main()
