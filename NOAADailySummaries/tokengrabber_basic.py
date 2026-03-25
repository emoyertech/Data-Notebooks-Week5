"""Basic Exercise 2 script (README-aligned).

This intentionally simple version does exactly what the README asks:
- Calls NOAA data endpoint twice (offset 1, then 1001)
- Defaults to January 2018 (README-compatible)
- Lets users choose year/month interactively or via flags

Usage:
  export NOAA_TOKEN="your_token_here"
  python tokengrabber_basic.py
    python tokengrabber_basic.py --year 2024 --month 2
    python tokengrabber_basic.py --start-date 2024-02-10 --end-date 2024-02-25
"""

import argparse
import calendar
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the basic fetcher."""
    parser = argparse.ArgumentParser(
        description="Fetch NOAA Daily Summaries for FIPS:10003 for a selected year and month."
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year to fetch. If omitted, prompt in TTY; otherwise defaults to 2018.",
    )
    parser.add_argument(
        "--month",
        type=str,
        default=None,
        help="Month to fetch (1-12, jan, january, etc). If omitted, prompt in TTY; otherwise defaults to 1 (January).",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Optional specific start date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="Optional specific end date in YYYY-MM-DD format.",
    )
    return parser.parse_args()


def resolve_year(explicit_year: int | None) -> int:
    """Resolve selected year from CLI, prompt, or default."""
    current_year = datetime.now().year
    min_year = 1700

    def validate_or_exit(year: int) -> int:
        if year < min_year or year > current_year:
            raise ValueError(f"Year must be between {min_year} and {current_year}")
        return year

    if explicit_year is not None:
        return validate_or_exit(explicit_year)

    if sys.stdin.isatty():
        while True:
            typed = input("Enter year (or q to quit): ").strip()
            if typed.lower() in {"q", "quit", "exit"}:
                raise ValueError("User cancelled input")
            if not typed:
                print("Year is required. Enter a year or q to quit.")
                continue
            try:
                return validate_or_exit(int(typed))
            except ValueError:
                print(f"Invalid year. Please enter a whole number between {min_year} and {current_year}, or q to quit.")
                continue

    return 2018


def resolve_month(explicit_month: str | None) -> int:
    """Resolve selected month from CLI, prompt, or default."""

    def parse_month_value(raw_value: str) -> int:
        value = raw_value.strip().lower()
        if not value:
            raise ValueError("Month is empty")

        if value.isdigit():
            month_number = int(value)
            if 1 <= month_number <= 12:
                return month_number
            raise ValueError("Month must be between 1 and 12")

        month_names = {
            name.lower(): index
            for index, name in enumerate(calendar.month_name)
            if name
        }
        month_abbrs = {
            name.lower(): index
            for index, name in enumerate(calendar.month_abbr)
            if name
        }
        if value in month_names:
            return month_names[value]
        if value in month_abbrs:
            return month_abbrs[value]
        raise ValueError("Unrecognized month")

    if explicit_month is not None:
        return parse_month_value(explicit_month)

    if sys.stdin.isatty():
        while True:
            typed = input("Enter month (1-12 or name, or q to quit): ").strip()
            if typed.lower() in {"q", "quit", "exit"}:
                raise ValueError("User cancelled input")
            if not typed:
                print("Month is required. Enter 1-12/name or q to quit.")
                continue
            try:
                return parse_month_value(typed)
            except ValueError:
                print("Invalid month. Use 1-12, jan, or january (or q to quit).")
                continue

    return 1


def _parse_iso_date(raw_value: str, field_name: str) -> datetime:
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format") from exc


def resolve_date_window(args: argparse.Namespace) -> tuple[str, str, str]:
    """Resolve start/end date window and filename label.

    Returns:
        tuple[startdate, enddate, label_for_filename]
    """

    if bool(args.start_date) != bool(args.end_date):
        raise ValueError("--start-date and --end-date must be provided together")

    if args.start_date and args.end_date:
        start_dt = _parse_iso_date(args.start_date, "--start-date")
        end_dt = _parse_iso_date(args.end_date, "--end-date")
        if start_dt > end_dt:
            raise ValueError("--start-date must be on or before --end-date")
        label = f"{start_dt.strftime('%Y%m%d')}_to_{end_dt.strftime('%Y%m%d')}"
        return args.start_date, args.end_date, label

    if sys.stdin.isatty():
        while True:
            use_custom = input("Use specific start/end dates? [y/N] (q to quit): ").strip().lower()
            if use_custom in {"q", "quit", "exit"}:
                raise ValueError("User cancelled input")
            if use_custom in {"", "n", "no"}:
                break
            if use_custom in {"y", "yes"}:
                while True:
                    start_raw = input("Enter start date (YYYY-MM-DD, or q to quit): ").strip()
                    if start_raw.lower() in {"q", "quit", "exit"}:
                        raise ValueError("User cancelled input")
                    end_raw = input("Enter end date (YYYY-MM-DD, or q to quit): ").strip()
                    if end_raw.lower() in {"q", "quit", "exit"}:
                        raise ValueError("User cancelled input")
                    if not start_raw or not end_raw:
                        print("Both dates are required. Try again or enter q to quit.")
                        continue

                    try:
                        start_dt = _parse_iso_date(start_raw, "Start date")
                        end_dt = _parse_iso_date(end_raw, "End date")
                    except ValueError as exc:
                        print(f"{exc}. Try again or enter q to quit.")
                        continue

                    if start_dt > end_dt:
                        print("Start date must be on or before end date. Try again or enter q to quit.")
                        continue

                    label = f"{start_dt.strftime('%Y%m%d')}_to_{end_dt.strftime('%Y%m%d')}"
                    return start_raw, end_raw, label
            else:
                print("Please answer y, n, or q.")

    selected_year = resolve_year(args.year)
    selected_month = resolve_month(args.month)
    month_label = calendar.month_abbr[selected_month].lower()
    last_day = calendar.monthrange(selected_year, selected_month)[1]
    startdate = f"{selected_year}-{selected_month:02d}-01"
    enddate = f"{selected_year}-{selected_month:02d}-{last_day:02d}"
    label = f"{month_label}_{selected_year}"
    return startdate, enddate, label

def _print_token_setup_steps() -> None:
    print("How to fix:")
    print("1) One-time run:")
    print('   NOAA_TOKEN="your_token_here" python tokengrabber_basic.py')
    print("2) Or set for this terminal session:")
    print('   export NOAA_TOKEN="your_token_here"')
    print("   python tokengrabber_basic.py")
    print("3) Optional: persist in zsh:")
    print('   echo \'export NOAA_TOKEN="your_token_here"\' >> ~/.zshrc')
    print("   source ~/.zshrc\n")


def get_token_or_help() -> str:
    """Return NOAA token or provide simple recovery instructions.

    Behavior:
    - Uses NOAA_TOKEN if already set.
    - If running interactively, offers a one-time prompt for token input.
    - Otherwise prints exact commands to fix and exits with a friendly error.
    """
    token = os.getenv("NOAA_TOKEN")
    if token:
        return token

    print("\nNOAA_TOKEN is not set.\n")

    if sys.stdin.isatty():
        while True:
            typed = input("Paste NOAA token (type help for setup, q to quit): ").strip()
            lowered = typed.lower()
            if lowered in {"q", "quit", "exit"}:
                raise ValueError("User cancelled input")
            if lowered in {"help", ""}:
                _print_token_setup_steps()
                continue
            return typed

    _print_token_setup_steps()

    raise ValueError("Missing NOAA_TOKEN")


def fetch_page(token: str, offset: int, startdate: str, enddate: str) -> dict:
    """Fetch one NOAA page for the selected date window."""
    params = {
        "datasetid": "GHCND",
        "locationid": "FIPS:10003",
        "startdate": startdate,
        "enddate": enddate,
        "limit": 1000,
        "offset": offset,
    }

    url = f"{BASE_URL}?{urlencode(params)}"
    request = Request(url, headers={"token": token}, method="GET")
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def save_payload(payload: dict, filename: str) -> Path:
    """Save one JSON payload to data/daily_summaries/<filename>."""
    out_dir = Path(__file__).parent / "data" / "daily_summaries"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / filename
    with open(out_file, "w") as file_handle:
        json.dump(payload, file_handle, indent=2)
    return out_file


def main() -> None:
    """Run both required requests and write both required output files."""
    args = parse_args()
    startdate, enddate, file_label = resolve_date_window(args)
    token = get_token_or_help()

    try:
        # README-required request #1: offset=1
        page_0 = fetch_page(token, offset=1, startdate=startdate, enddate=enddate)
        file_0 = save_payload(page_0, f"daily_summaries_FIPS10003_{file_label}_0.json")

        # README-required request #2: offset=1001
        page_1 = fetch_page(token, offset=1001, startdate=startdate, enddate=enddate)
        file_1 = save_payload(page_1, f"daily_summaries_FIPS10003_{file_label}_1.json")

    except HTTPError as exc:
        print(f"NOAA API request failed (HTTP {exc.code}).")
        if exc.code in (401, 403):
            print("Your token may be missing, invalid, or not authorized.")
            print("Verify NOAA_TOKEN and try again.")
        raise
    except URLError:
        print("Could not reach NOAA API. Check internet connection and try again.")
        raise

    print(f"Saved data for {startdate} through {enddate}:")
    print(f"- {file_0}")
    print(f"- {file_1}")


if __name__ == "__main__":
    main()
