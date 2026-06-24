import requests
import json
import lzma
from datetime import datetime

# 1. Use secure HTTPS and define a clear User-Agent header to prevent blocking
overpass_url = "https://overpass-api.de/api/interpreter"
headers = {
    "User-Agent": "LithuaniaCamServerAutomation/1.0 (GitHub Action Workflow)"
}

overpass_query = """
[out:json][timeout:60];
area["ISO3166-1"="LT"][admin_level=2]->.searchArea;
(
  node["highway"="speed_camera"](area.searchArea);
  node["enforcement"~"traffic_signals|average_speed"](area.searchArea);
  node["man_made"="surveillance"]["camera:type"~"speed_camera|red_light"](area.searchArea);
  node["man_made"="surveillance"]["surveillance:type"="ALPR"](area.searchArea);
);
out center;
"""

print("Sending request to Overpass API...")
response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers)

# Check if the server actually returned a successful 200 OK status
if response.status_code != 200:
    print(f"Error: Server responded with status code {response.status_code}")
    print("Response text from server:")
    print(response.text)
    exit(1)

try:
    data = response.json()
except Exception as e:
    print("Failed to decode JSON. Server did not send valid data.")
    print("Response text received:")
    print(response.text)
    raise e

print(f"Successfully retrieved {len(data.get('elements', []))} camera nodes.")

today = datetime.now().strftime("%Y-%m-%d")
excam_filename = "lithuania_cams.excam"

# 2. Write and compress directly to the ExCam (XZ) format
with lzma.open(excam_filename, "wt", encoding="utf-8") as f:
    f.write(json.dumps({"name": "Lithuania OSM Cameras", "date": today}) + "\n")
    
    for element in data.get('elements', []):
        # Default camera type is 1 (Speed camera)
        cam_type = 1 
        
        # Smart detection based on tags
        tags = element.get('tags', {})
        if tags.get('enforcement') == 'traffic_signals' or tags.get('camera:type') == 'red_light':
            cam_type = 2 # Red light camera
        elif tags.get('enforcement') == 'average_speed':
            cam_type = 3 # Average speed section point

        cam_data = {
            "lat": element['lat'],
            "lon": element['lon'],
            "type": cam_type
        }
        
        # Include speed limit if available
        if 'maxspeed' in tags:
            try:
                cam_data["speed"] = int(tags['maxspeed'])
            except ValueError:
                pass
                
        f.write(json.dumps(cam_data) + "\n")

# 3. Create the Highway Radar Update Link JSON
link_data = {
    "_link": {
        "dataUrl": "https://github.com/cam-server/cam-server/raw/main/lithuania_cams.excam",
        "date": today
    }
}
with open("update_link.json", "w") as f:
    json.dump(link_data, f)

print("ExCam database and link file generated successfully!")
