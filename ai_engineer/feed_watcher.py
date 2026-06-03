import os
import json
import requests
from openai import OpenAI

# 1. Fetch live earthquake data (using USGS as the primary example)
FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
response = requests.get(FEED_URL)
live_data = response.json()

# Extract the properties of the first earthquake to analyze the schema
if not live_data.get("features"):
    print("No earthquakes found right now, skipping audit.")
    exit(0)

live_properties = live_data["features"][0]["properties"]
live_schema_keys = list(live_properties.keys())

# 2. Load our known "safe" schema from Memory
memory_file = ".memory/usgs_schema_snapshot.json"
try:
    with open(memory_file, "r") as f:
        known_schema = json.load(f)
except FileNotFoundError:
    # If it's the first run, save the current schema and exit safely
    os.makedirs(".memory", exist_ok=True)
    with open(memory_file, "w") as f:
        json.dump(live_schema_keys, f)
    print("Baseline schema saved. Exiting.")
    exit(0)

# 3. Detect Drift
added_keys = [k for k in live_schema_keys if k not in known_schema]
missing_keys = [k for k in known_schema if k not in live_schema_keys]

if not added_keys and not missing_keys:
    print("Schema is stable. No action required.")
    exit(0)

# 4. If broken, engage the LLM to write an engineering report
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

prompt = f"""
You are a Staff Software Engineer maintaining a Home Assistant integration for global earthquakes.
The upstream USGS GeoJSON feed schema has changed.

Missing Fields (Removed by upstream): {missing_keys}
New Fields (Added by upstream): {added_keys}

Write a short, highly technical GitHub Issue report for the maintainer.
Include:
1. The exact changes detected.
2. The likely impact on Home Assistant sensors (e.g., if 'mag' is missing, the magnitude sensor breaks).
3. A suggested code fix or fallback strategy in Python.
"""

completion = client.chat.completions.create(
    model="gpt-4o-mini", # Using the cheapest, fastest reasoning model
    messages=[{"role": "user", "content": prompt}]
)

report_content = completion.choices[0].message.content

# 5. Save the report and trigger GitHub Actions to open the issue
with open("ai_report.md", "w") as f:
    f.write(report_content)

# Tell the GitHub Action runner that a change was detected
with open(os.environ['GITHUB_ENV'], 'a') as f:
    f.write("SCHEMA_CHANGED=true\n")