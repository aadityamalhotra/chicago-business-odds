import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CENSUS_API_KEY")

BASE_URL = "https://api.census.gov/data/2024/acs/acs5"
VARS = "B01003_001E,B19013_001E"  # total population, median household income

params = {
    "get": f"NAME,{VARS}",
    "for": "tract:*",
    "in": "state:17 county:031",
    "key": API_KEY,
}

resp = requests.get(BASE_URL, params=params)
resp.raise_for_status()
rows = resp.json()

df = pd.DataFrame(rows[1:], columns=rows[0])
df = df.rename(columns={"B01003_001E": "population", "B19013_001E": "median_income"})
df["population"] = pd.to_numeric(df["population"], errors="coerce")
df["median_income"] = pd.to_numeric(df["median_income"], errors="coerce")
df["GEOID"] = df["state"] + df["county"] + df["tract"]

df.to_csv("data/raw/census_tract_acs.csv", index=False)
print(f"Pulled {len(df)} Cook County tracts.")
print(df.head())
