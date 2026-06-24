import requests
import json
import lzma
from datetime import datetime

# 1. Query the Overpass API directly
overpass_url = "http://overpass-api.de/api/interpreter"
overpass_query = """
[out:json][timeout:25];
area["ISO3166-1"="LT"][admin_level=2]->.searchArea;
(
  node["highway"="speed_camera"](area.searchArea);
);
out center;
"""
response = requests.post(overpass_url, data={'data': overpass_query})
data = response.json()

today = datetime.now().strftime("%Y-%m-%d")
excam_filename = "lithuania_cams.excam"

# 2. Write and compress directly to the ExCam (XZ) format
with lzma.open(excam_filename, "wt", encoding="utf-8") as f:
    # First line is always the ExCam Metadata
    f.write(json.dumps({"name": "Lithuania OSM Cameras", "date": today}) + "\n")
    
    # Subsequent lines are the cameras
    for element in data['elements']:
        cam_data = {
            "lat": element['lat'],
            "lon": element['lon'],
            "type": 1 # Example ExCam ID for Speed Camera
        }
        f.write(json.dumps(cam_data) + "\n")

# 3. Create the Highway Radar Update Link JSON
link_data = {
    "_link": {
        "dataUrl": "https://[YOUR-GITHUB-USERNAME].github.io/[YOUR-REPO]/lithuania_cams.excam",
        "date": today
    }
}
with open("update_link.json", "w") as f:
    json.dump(link_data, f)
