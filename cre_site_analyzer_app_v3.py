
import streamlit as st
import requests
from utils import get_here_traffic_data_v7

st.title("CRE Site Analyzer - Traffic v7 Enabled")

address = st.text_input("Enter a property address:")
if address:
    lat = 40.758  # dummy value for demo
    lon = -73.9855
    st.write(f"📍 Coordinates: {lat}, {lon}")
    traffic = get_here_traffic_data_v7(lat, lon, st.secrets["HERE_API_KEY"])
    if "error" in traffic:
        st.error(traffic["error"])
    else:
        st.success("✅ Live Traffic Data")
        st.write(traffic)
