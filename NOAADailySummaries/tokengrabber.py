import requests
import json

# You'll need a NOAA API token from here:
# https://www.ncdc.noaa.gov/cdo-web/token

TOKEN = "DWcmXaaqaQwvUtSOQevwBcMWtRGXWyIa"  # Get this from NOAA

headers = {"token": TOKEN}
base_url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"

params = {
    "datasetid": "GHCND",
    "locationid": "FIPS:10003",
    "startdate": "2018-01-01",
    "enddate": "2018-01-31",
    "limit": 1000
}

# First request (offset 1)
params["offset"] = 1
response1 = requests.get(base_url, headers=headers, params=params)
with open("data/daily_summaries/daily_summaries_FIPS10003_jan_2018_0.json", "w") as f:
    json.dump(response1.json(), f, indent=2)

# Second request (offset 1001)
params["offset"] = 1001
response2 = requests.get(base_url, headers=headers, params=params)
with open("data/daily_summaries/daily_summaries_FIPS10003_jan_2018_1.json", "w") as f:
    json.dump(response2.json(), f, indent=2)

print("✅ Data saved!")