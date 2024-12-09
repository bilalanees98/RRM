import pandas as pd
import joblib
import numpy as np
import json


def load_historical_data():
    # Paths for assets
    historical_csv_path = "assets/actual_crop_data_with_simulated_weather_data.csv"
    geojson_path = "assets/simulate_rice_grid_1000x1000.geojson"
    all_districts_geojson_path = "assets/five_punjab_districts.geojson"

    # Load historical data
    historical_data = pd.read_csv(historical_csv_path)
    historical_data["Year"] = historical_data["Year"].str.split("-").str[0].astype(int)

    # Load GeoJSON data
    with open(geojson_path, "r") as f:
        geojson_data = json.load(f)
    with open(all_districts_geojson_path, "r") as f:
        all_districts_geojson = json.load(f)

    return historical_data, geojson_data, all_districts_geojson


def get_districts_data(historical_data, district_name=None):
    
    if district_name:
        district_data = historical_data[historical_data["District"] == district_name]
        if district_data.empty:
            return None
        return {
            "District": district_name,
            "Historical_Data": {
                "Years": district_data["Year"].tolist(),
                "Area": district_data["Area"].tolist(),
                "Production": district_data["Production"].tolist(),
                "Yield": district_data["Crop_Yield"].tolist(),
            }
        }
    return historical_data["District"].unique().tolist()


def predict_yield(historical_data, district_name):
    # Hardcoded values for area and weather data
    hardcoded_data = {
        "Bhawalnagar": {
            "Area": 110.0,
            "Weather": {
                "Plantation_Temperature": 29.0,
                "Plantation_Humidity": 68.0,
                "Plantation_Rainfall": 140.0,
                "Growth_Temperature": 34.0,
                "Growth_Humidity": 75.0,
                "Growth_Rainfall": 280.0,
                "Harvest_Temperature": 20.0,
                "Harvest_Humidity": 48.0,
                "Harvest_Rainfall": 45.0,
            },
        },
        "Sheikhupura": {
            "Area": 232.0,
            "Weather": {
                "Plantation_Temperature": 30.0,
                "Plantation_Humidity": 70.0,
                "Plantation_Rainfall": 150.0,
                "Growth_Temperature": 35.0,
                "Growth_Humidity": 80.0,
                "Growth_Rainfall": 300.0,
                "Harvest_Temperature": 25.0,
                "Harvest_Humidity": 50.0,
                "Harvest_Rainfall": 50.0,
            },
        },
        "Jhang": {
            "Area": 154.0,
            "Weather": {
                "Plantation_Temperature": 28.0,
                "Plantation_Humidity": 65.0,
                "Plantation_Rainfall": 130.0,
                "Growth_Temperature": 33.0,
                "Growth_Humidity": 78.0,
                "Growth_Rainfall": 250.0,
                "Harvest_Temperature": 22.0,
                "Harvest_Humidity": 45.0,
                "Harvest_Rainfall": 40.0,
            },
        },
        "Sialkot": {
            "Area": 190.0,
            "Weather": {
                "Plantation_Temperature": 27.0,
                "Plantation_Humidity": 67.0,
                "Plantation_Rainfall": 145.0,
                "Growth_Temperature": 32.0,
                "Growth_Humidity": 76.0,
                "Growth_Rainfall": 270.0,
                "Harvest_Temperature": 21.0,
                "Harvest_Humidity": 46.0,
                "Harvest_Rainfall": 42.0,
            },
        },
        "Hafizabad": {
            "Area": 156.0,
            "Weather": {
                "Plantation_Temperature": 29.5,
                "Plantation_Humidity": 69.0,
                "Plantation_Rainfall": 135.0,
                "Growth_Temperature": 34.5,
                "Growth_Humidity": 77.0,
                "Growth_Rainfall": 260.0,
                "Harvest_Temperature": 23.0,
                "Harvest_Humidity": 47.0,
                "Harvest_Rainfall": 43.0,
            },
        },
        "Pakpattan": {
            "Area": 84.5,
            "Weather": {
                "Plantation_Temperature": 28.5,
                "Plantation_Humidity": 66.0,
                "Plantation_Rainfall": 140.0,
                "Growth_Temperature": 33.5,
                "Growth_Humidity": 74.0,
                "Growth_Rainfall": 275.0,
                "Harvest_Temperature": 22.0,
                "Harvest_Humidity": 46.0,
                "Harvest_Rainfall": 44.0,
            },
        },
    }


    # Check if the district exists in hardcoded data
    if district_name not in hardcoded_data:
        return None

    # Get fixed values for the district
    district_data = hardcoded_data[district_name]
    rice_area = district_data["Area"]
    weather = district_data["Weather"]

    # Prepare input for the model
    inputs = np.array([[
        weather["Plantation_Temperature"], weather["Plantation_Humidity"], weather["Plantation_Rainfall"],
        weather["Growth_Temperature"], weather["Growth_Humidity"], weather["Growth_Rainfall"],
        weather["Harvest_Temperature"], weather["Harvest_Humidity"], weather["Harvest_Rainfall"]
    ]])

    # Load the updated model trained with the new dataset
    model = joblib.load("assets/rf_yield_prediction_model.pkl")
    predicted_yield = model.predict(inputs)[0]
    predicted_production = (predicted_yield * rice_area) / 1000  # Convert from kg to tonnes

    return {
        "District": district_name,
        "Predicted_Production": round(predicted_production, 2),
        "Predicted_Yield": round(predicted_yield, 2),
        "Inputs": {
            "Area": round(rice_area, 2),
            "Plantation_Temperature": round(weather["Plantation_Temperature"], 2),
            "Plantation_Humidity": round(weather["Plantation_Humidity"], 2),
            "Plantation_Rainfall": round(weather["Plantation_Rainfall"], 2),
            "Growth_Temperature": round(weather["Growth_Temperature"], 2),
            "Growth_Humidity": round(weather["Growth_Humidity"], 2),
            "Growth_Rainfall": round(weather["Growth_Rainfall"], 2),
            "Harvest_Temperature": round(weather["Harvest_Temperature"], 2),
            "Harvest_Humidity": round(weather["Harvest_Humidity"], 2),
            "Harvest_Rainfall": round(weather["Harvest_Rainfall"], 2),
        }
    }



def get_district_geojson(geojson_data, district_name):
    if district_name == 'Bhawalnagar':
         district_name='Bahawalnagar'
    features = [f for f in geojson_data["features"] if f["properties"].get("district") == district_name]
    return {"type": "FeatureCollection", "features": features} if features else None
