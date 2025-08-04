
import requests

def get_here_traffic_data_v7(lat, lon, here_api_key):
    top = lat + 0.005
    left = lon - 0.005
    bottom = lat - 0.005
    right = lon + 0.005

    url = "https://data.traffic.hereapi.com/v7/flow"
    params = {
        "in": f"boundingBox:{bottom},{left},{top},{right}",
        "locationReferencing": "shape",
        "apikey": here_api_key
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return {"error": f"HERE API failed ({response.status_code})", "details": response.text}

    data = response.json()
    try:
        first_segment = data["flows"][0]
        return {
            "jam_factor": first_segment.get("jamFactor"),
            "free_flow_speed": first_segment.get("freeFlowSpeed"),
            "current_speed": first_segment.get("currentSpeed"),
            "confidence": first_segment.get("confidence")
        }
    except Exception as e:
        return {"error": f"No traffic data available - {str(e)}"}
