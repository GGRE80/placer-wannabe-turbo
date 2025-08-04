
import streamlit as st
from utils import get_here_traffic_data_v7

st.title("CRE Site Analyzer - HERE Traffic v7 Enabled")

address = st.text_input("Enter a property address:")

# Temporary fixed coordinates for Times Square
lat, lon = 40.758, -73.9855
st.write(f"📍 Coordinates: {lat}, {lon}")

if address:
    st.info("Fetching real-time traffic data using HERE API v7...")
    traffic = get_here_traffic_data_v7(lat, lon, st.secrets["HERE_API_KEY"])

    if "error" in traffic:
        st.error(f"{traffic['error']}")
        if "details" in traffic:
            st.text(traffic["details"])
    else:
        st.success("✅ Live Traffic Data Retrieved")
        st.json(traffic)
