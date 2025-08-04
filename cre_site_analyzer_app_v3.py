
import streamlit as st
import requests
import openai

# Load secrets
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
CENSUS_API_KEY = st.secrets["CENSUS_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
HERE_API_KEY = st.secrets["HERE_API_KEY"]

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def geocode_address(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_API_KEY}
    response = requests.get(url, params=params).json()
    if response["status"] == "OK":
        location = response["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        return None, None

def get_here_traffic_data(lat, lon):
    url = f"https://traffic.ls.hereapi.com/traffic/6.3/flow.json"
    params = {
        "prox": f"{lat},{lon},500",
        "apiKey": HERE_API_KEY,
        "responseattributes": "sh,fc"
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return {"error": "HERE API failed"}
    data = response.json()
    try:
        flow = data["RWS"][0]["RW"][0]["FIS"][0]["FI"][0]["CF"][0]
        return {
            "jam_factor": round(flow["JF"], 2),
            "free_flow_speed": round(flow["FF"], 2),
            "current_speed": round(flow["SU"], 2),
            "confidence": round(flow["CN"], 2)
        }
    except Exception:
        return {"error": "Traffic data not available"}

def get_nearby_places(address, radius=500):
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}"
    geo_response = requests.get(geocode_url).json()
    if geo_response["status"] != "OK":
        return {"error": "Geocode failed."}
    location = geo_response["results"][0]["geometry"]["location"]
    lat, lng = location["lat"], location["lng"]
    places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&key={GOOGLE_API_KEY}"
    places_response = requests.get(places_url).json()
    results = places_response.get("results", [])
    return [{"name": place["name"], "types": place["types"]} for place in results]

def get_demographics(zipcode):
    census_url = f"https://api.census.gov/data/2020/acs/acs5/profile?get=DP03_0062E,DP03_0063E&for=zip%20code%20tabulation%20area:{zipcode}&key={CENSUS_API_KEY}"
    response = requests.get(census_url).json()
    if "error" in response:
        return {"error": "Census API failed"}
    headers = response[0]
    values = response[1]
    data = dict(zip(headers, values))
    return {
        "Median Household Income": f"${data.get('DP03_0062E', 'N/A')}",
        "Poverty Rate Estimate": data.get("DP03_0063E", "N/A") + "%"
    }

def compute_site_traffic_score(places, demographics):
    score = 0
    anchor_keywords = ["walmart", "starbucks", "target", "whole foods", "costco", "kroger", "aldi"]
    score += len(places) * 2
    for place in places:
        if any(anchor in place["name"].lower() for anchor in anchor_keywords):
            score += 20
    try:
        income = int(demographics.get("Median Household Income", "$0").replace("$", "").replace(",", ""))
        if income > 60000: score += 15
        elif income > 40000: score += 10
        else: score += 5
    except: score += 0
    return min(score, 100)

def generate_summary(address, places, demographics, traffic_score, traffic_info):
    prompt = f"""
You are an AI commercial real estate analyst. Analyze the following site:
Address: {address}
Nearby Businesses: {places}
Demographics: {demographics}
Estimated Foot Traffic Score (0-100): {traffic_score}
Live Traffic Info: {traffic_info}

Give a brief site summary including:
- Commercial viability
- Traffic strength
- Investment outlook
- Anchor co-tenancy or notable patterns
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    st.session_state["last_token_usage"] = response.usage.total_tokens
    return response.choices[0].message.content.strip()

def render_google_map(address):
    embed_url = f"https://www.google.com/maps/embed/v1/place?key={GOOGLE_API_KEY}&q={address.replace(' ', '+')}&layer=traffic"
    st.components.v1.iframe(embed_url, width=700, height=450)

st.set_page_config(page_title="Placer Wannabe Turbo", layout="centered")
st.title("📍 Placer Wannabe Turbo – CRE Traffic Enhanced")

address = st.text_input("Enter a property address:")
zipcode = st.text_input("Enter ZIP code (for demographics)")

if st.button("Analyze Site") and address and zipcode:
    with st.spinner("Analyzing..."):
        lat, lon = geocode_address(address)
        if not lat or not lon:
            st.error("Geocoding failed.")
        else:
            places = get_nearby_places(address)
            demographics = get_demographics(zipcode)
            traffic_info = get_here_traffic_data(lat, lon)
            if "error" in places or "error" in demographics or "error" in traffic_info:
                st.error("API error. Please verify inputs.")
            else:
                st.subheader("🏬 Nearby Businesses")
                st.write(places)

                st.subheader("👥 Demographics")
                st.write(demographics)

                st.subheader("🚦 Real-Time Traffic")
                st.write(traffic_info)

                traffic_score = compute_site_traffic_score(places, demographics)
                st.metric("Estimated Foot Traffic Score", f"{traffic_score}/100")

                st.subheader("🗺️ Live Traffic Map")
                render_google_map(address)

                st.subheader("🧠 AI Site Summary")
                summary = generate_summary(address, places, demographics, traffic_score, traffic_info)
                st.write(summary)

                if "last_token_usage" in st.session_state:
                    st.info(f"🧾 Estimated OpenAI token usage: {st.session_state['last_token_usage']} tokens")
