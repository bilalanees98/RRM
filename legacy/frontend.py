# to run: streamlit run frontend.py 
import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# Backend API URL
API_URL = "http://127.0.0.1:5000"

# Title and Instructions
st.title("Punjab District Rice Map")
st.markdown("### Select a district to view its rice-producing map, historical data, and predictions.")

# Sidebar: Fetch Districts
st.sidebar.title("Select District")
try:
    response = requests.get(f"{API_URL}/districts")
    if response.status_code == 200:
        districts = response.json()["districts"]
        selected_district = st.sidebar.selectbox("Districts", sorted(districts))
    else:
        st.sidebar.error("Failed to load districts")
        selected_district = None
except requests.exceptions.RequestException:
    st.sidebar.error("Backend not reachable")
    selected_district = None

# Display Map, Historical Data, and Predictions for Selected District
if selected_district:
    st.markdown(f"### Selected District: {selected_district}")

    # Fetch and Display Historical Data
    st.markdown("#### Historical Trends")
    try:
        response = requests.get(f"{API_URL}/district/{selected_district}/historical")
        if response.status_code == 200:
            historical_data = response.json()["Historical_Data"]
            st.line_chart(
                {
                    "Area": historical_data["Area"],
                    "Production": historical_data["Production"],
                    # "Yield": historical_data["Yield"],
                }
            )
        else:
            st.error(f"Failed to load historical data for {selected_district}")
    except requests.exceptions.RequestException:
        st.error("Backend not reachable for historical data.")

    # Fetch and Display District Map
    st.markdown("#### Rice-Producing Map")
    try:
        response = requests.get(f"{API_URL}/district/{selected_district}/map")
        if response.status_code == 200:
            district_geojson = response.json()

            # Calculate center and zoom level
            lats = []
            lngs = []
            for feature in district_geojson["features"]:
                geometry_type = feature["geometry"]["type"]
                if geometry_type == "Polygon":
                    for ring in feature["geometry"]["coordinates"]:
                        for coord in ring:
                            lngs.append(coord[0])  # Longitude
                            lats.append(coord[1])  # Latitude
                elif geometry_type == "Point":
                    lngs.append(feature["geometry"]["coordinates"][0])
                    lats.append(feature["geometry"]["coordinates"][1])

            # Compute the center
            if lats and lngs:
                center_lat = sum(lats) / len(lats)
                center_lng = sum(lngs) / len(lngs)
            else:
                center_lat, center_lng = 30.3753, 69.3451  # Default center (Punjab, Pakistan)

            # Create Folium Map
            m = folium.Map(location=[center_lat, center_lng], zoom_start=10)  # Adjust zoom for districts
            folium.GeoJson(
                district_geojson,
                style_function=lambda feature: {
                    "fillColor": feature["properties"]["fill"],
                    "color": "black",
                    "weight": 1,
                    "fillOpacity": 0.6,
                }
            ).add_to(m)

            st_folium(m, width=700, height=500)
        else:
            st.error(f"Failed to load map data for {selected_district}")
    except requests.exceptions.RequestException:
        st.error("Backend not reachable for map data.")


    # Fetch and Display Predictions
    st.markdown("#### Predictions for the Current Year")
    try:
        response = requests.post(f"{API_URL}/district/{selected_district}/predict")
        if response.status_code == 200:
            prediction = response.json()
            st.write(f"**Expected Area:** {prediction['Inputs']['Area']} hectares")
            st.write(f"**Expected Yield:** {round(prediction['Predicted_Production'] / prediction['Inputs']['Area'], 2)} tons/hectare")
            st.write(f"**Expected Production:** {prediction['Predicted_Production']} tons")
            st.markdown("*Calculated in September 2024*")
        else:
            st.error(f"Failed to load predictions for {selected_district}")
    except requests.exceptions.RequestException:
        st.error("Backend not reachable for predictions.")
