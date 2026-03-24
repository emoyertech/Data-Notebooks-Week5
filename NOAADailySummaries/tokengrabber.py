"""NOAA data fetch script.

This module downloads Daily Summaries data from NOAA and stores each page
response as a JSON file under data/daily_summaries.

Design notes:
- Uses urllib from Python standard library (no external HTTP package required).
- Uses pagination (offset/limit) until the final page is reached.
- Returns saved file paths so other modules can chain this step.
"""

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"


def fetch_daily_summaries(
    token,
    output_dir=None,
    datasetid="GHCND",
    locationid="FIPS:10003",
    startdate="2018-01-01",
    enddate="2018-01-31",
    limit=1000,
):
    """Fetch NOAA daily summaries and persist paginated responses to JSON files.

    Args:
        token: NOAA API token.
        output_dir: Target directory for saved JSON pages.
        datasetid/locationid/startdate/enddate/limit: NOAA query parameters.

    Returns:
        list[Path]: Paths of JSON files written for each fetched page.
    """
    if not token:
        raise ValueError("Missing NOAA token. Pass token=... or set NOAA_TOKEN.")

    if output_dir is None:
        output_dir = Path(__file__).parent / "data" / "daily_summaries"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    headers = {"token": token}
    offset = 1
    page = 0
    saved_files = []

    while True:
        # Build one paginated request.
        params = {
            "datasetid": datasetid,
            "locationid": locationid,
            "startdate": startdate,
            "enddate": enddate,
            "limit": limit,
            "offset": offset,
        }
        query_url = f"{BASE_URL}?{urlencode(params)}"
        request = Request(query_url, headers=headers, method="GET")
        with urlopen(request, timeout=30) as response:
            status_code = getattr(response, "status", None)
            if status_code is not None and status_code >= 400:
                raise RuntimeError(f"NOAA request failed with status {status_code}")
            payload = json.loads(response.read().decode("utf-8"))
        results = payload.get("results", []) if isinstance(payload, dict) else []

        # Save each page so source data remains inspectable and reproducible.
        filename = f"daily_summaries_{locationid.replace(':', '')}_{startdate}_{enddate}_{page}.json"
        out_file = output_dir / filename
        with open(out_file, "w") as file_handle:
            json.dump(payload, file_handle, indent=2)
        saved_files.append(out_file)

        # Stop when NOAA returned fewer rows than limit (last page).
        if not results or len(results) < limit:
            break

        # Continue pagination.
        offset += limit
        page += 1

    return saved_files


if __name__ == "__main__":
    # CLI mode: read token from environment and fetch into default folder.
    token = os.getenv("NOAA_TOKEN")
    files = fetch_daily_summaries(token=token)
    print(f"✅ Data saved: {len(files)} file(s)")
    for file_path in files:
        print(f" - {file_path}")