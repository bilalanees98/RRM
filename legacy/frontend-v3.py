# to run: streamlit run frontend-v3.py
import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# Backend API URL
API_URL = "http://127.0.0.1:5000"

# Title and Instructions
st.title("Punjab District Rice Insights")
st.markdown("### Navigate between Supply and Trends sections for insights.")

# Sidebar Navigation
section = st.sidebar.radio("Sections", ["Supply", "Trends"])

if section == "Supply":
    # Existing Functionality (Supply Section)
    st.header("Supply: District-Wise Insights")
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

    # Fetch All Districts GeoJSON from Backend
    try:
        response = requests.get(f"{API_URL}/all-districts")
        if response.status_code == 200:
            all_districts_geojson = response.json()
        else:
            st.error("Failed to load all-districts GeoJSON.")
            all_districts_geojson = {"type": "FeatureCollection", "features": []}
    except requests.exceptions.RequestException:
        st.error("Backend not reachable for all-districts GeoJSON.")
        all_districts_geojson = {"type": "FeatureCollection", "features": []}

    # Display Map, Historical Data, and Predictions for Selected District
    if selected_district:
        st.markdown(f"### Selected District: {selected_district}")

        # Fetch and Display Historical Data
        st.markdown("#### Historical Trends")
        try:
            response = requests.get(f"{API_URL}/district/{selected_district}/historical")
            if response.status_code == 200:
                historical_data = response.json()["Historical_Data"]

                # Scale the data to '000 hectares' and '000 tonnes'
                scaled_area = [x / 1000 for x in historical_data["Area"]]
                scaled_production = [x / 1000 for x in historical_data["Production"]]

                st.line_chart(
                    {
                        "Area ('000 hectares)": scaled_area,
                        "Production ('000 tonnes)": scaled_production,
                    }
                )
            else:
                st.error(f"Failed to load historical data for {selected_district}")
        except requests.exceptions.RequestException:
            st.error("Backend not reachable for historical data.")

        # Fetch and Display District Map
        st.markdown("#### Rice-production Map")
        try:
            response = requests.get(f"{API_URL}/district/{selected_district}/map")
            if response.status_code == 200:
                district_geojson = response.json()
            else:
                st.error(f"Failed to load map data for {selected_district}")
                district_geojson = {"type": "FeatureCollection", "features": []}
        except requests.exceptions.RequestException:
            st.error("Backend not reachable for map data.")
            district_geojson = {"type": "FeatureCollection", "features": []}

        # Validate the district GeoJSON
        if not district_geojson["features"]:
            st.error("No features found for the selected district. Check the GeoJSON.")
        else:
            # Create the map
            m = folium.Map(location=[30.3753, 69.3451], zoom_start=6)

            # Add all districts layer
            folium.GeoJson(
                all_districts_geojson,
                style_function=lambda feature: {
                    "fillColor": "gray",
                    "color": "black",
                    "weight": 0.5,
                    "fillOpacity": 0.3,
                },
            ).add_to(m)

            # Highlight selected district
            folium.GeoJson(
                all_districts_geojson,
                style_function=lambda feature: {
                    "fillColor": "blue" if feature["properties"].get("district") == selected_district else "gray",
                    "color": "black",
                    "weight": 2 if feature["properties"].get("district") == selected_district else 0.5,
                    "fillOpacity": 0.5 if feature["properties"].get("district") == selected_district else 0.3,
                },
            ).add_to(m)

            # Overlay the grid for the selected district
            folium.GeoJson(
                district_geojson,
                style_function=lambda feature: {
                    "fillColor": feature["properties"]["fill"] if "fill" in feature["properties"] else "yellow",
                    "color": "black",
                    "weight": 1,
                    "fillOpacity": 0.6,
                },
            ).add_to(m)

            st_folium(m, width=1000, height=500)

        # Fetch and Display Predictions
        st.markdown("#### Predictions for the Current Year")
        try:
            response = requests.post(f"{API_URL}/district/{selected_district}/predict")
            if response.status_code == 200:
                prediction = response.json()
                st.write(f"**Expected Area:** {prediction['Inputs']['Area']} (000 hectares)")
                st.write(f"**Expected Yield:** {round(prediction['Predicted_Production'] / prediction['Inputs']['Area'], 2)} tons/hectare")
                st.write(f"**Expected Production:** {prediction['Predicted_Production']} (000 tons)")
                st.markdown("*Calculated in September 2024*")
            else:
                st.error(f"Failed to load predictions for {selected_district}")
        except requests.exceptions.RequestException:
            st.error("Backend not reachable for predictions.")

elif section == "Trends":
    # New Functionality (Trends Section)
    st.header("Trends: News Insights")
    
    # Display the last execution date
    try:
        response = requests.get(f"{API_URL}/news/dates")
        if response.status_code == 200:
            available_dates = response.json().get("available_dates", [])
            last_execution_date = available_dates[-1] if available_dates else "No data available"
            st.write(f"**Last Execution Date:** {last_execution_date}")
        else:
            st.error("Failed to fetch the last execution date.")
    except requests.exceptions.RequestException:
        st.error("Backend not reachable for fetching dates.")

    # Trigger the cronjob
    if st.button("Run News Insights Processing"):
        try:
            response = requests.post(f"{API_URL}/news/trigger")
            if response.status_code == 200:
                st.success("News insights processing triggered successfully.")
            else:
                st.error("Failed to trigger the news insights processing.")
        except requests.exceptions.RequestException:
            st.error("Backend not reachable for triggering news insights.")

    # Dropdown to select a date
    if available_dates:
        selected_date = st.selectbox("Select a Date", sorted(available_dates, reverse=True))
        if st.button("Fetch Insights"):
            try:
                response = requests.get(f"{API_URL}/news/insights/{selected_date}")
                if response.status_code == 200:
                    insights = response.json().get("insights", [])
                    for insight in insights:
                        st.markdown(f"### {insight['title']}")
                        st.write(insight["insight"])
                        st.write(f"[Source]({insight['url']})")
                else:
                    st.error(f"No insights available for {selected_date}.")
            except requests.exceptions.RequestException:
                st.error("Backend not reachable for fetching insights.")
    else:
        st.info("No insights available. Run the news insights processing first.")
