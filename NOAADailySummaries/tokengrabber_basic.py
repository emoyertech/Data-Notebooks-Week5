"""Basic Exercise 2 script (README-aligned).

This intentionally simple version does exactly what the README asks:
- Calls NOAA data endpoint twice (offset 1, then 1001)
- Saves to the exact required filenames
  - daily_summaries_FIPS10003_jan_2018_0.json
  - daily_summaries_FIPS10003_jan_2018_1.json

Usage:
  export NOAA_TOKEN="your_token_here"
  python tokengrabber_basic.py
"""

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"


def fetch_page(token: str, offset: int) -> dict:
    """Fetch one NOAA page for the fixed README parameters."""
    params = {
        "datasetid": "GHCND",
        "locationid": "FIPS:10003",
        "startdate": "2018-01-01",
        "enddate": "2018-01-31",
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
    token = os.getenv("NOAA_TOKEN")
    if not token:
        raise ValueError("Set NOAA_TOKEN first, then run again.")

    # README-required request #1: offset=1
    page_0 = fetch_page(token, offset=1)
    file_0 = save_payload(page_0, "daily_summaries_FIPS10003_jan_2018_0.json")

    # README-required request #2: offset=1001
    page_1 = fetch_page(token, offset=1001)
    file_1 = save_payload(page_1, "daily_summaries_FIPS10003_jan_2018_1.json")

    print("Saved:")
    print(f"- {file_0}")
    print(f"- {file_1}")


if __name__ == "__main__":
    main()
