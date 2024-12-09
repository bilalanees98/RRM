# to run: python app.py
# news api: priv key = afc4106788834f80bf24ca001dae299f
from flask import Flask, jsonify, request
import pandas as pd
import joblib
import numpy as np
import json

app = Flask(__name__)

# Load Historical Data from CSV
historical_csv_path = "assets/simulated_crop_yield_with_weather_and_humidity.csv"
historical_data = pd.read_csv(historical_csv_path)

# Ensure the data is clean and structured
historical_data["Year"] = historical_data["Year"].str.split("-").str[0].astype(int)
print("Loaded Historical Data Sample:")
print(historical_data.head())

# Load the trained model
model = joblib.load("assets/yield_prediction_model.pkl")  # Ensure the model is in the same directory

# Load Simulated GeoJSON Map Data
geojson_path = "assets/simulate_rice_grid_1000x1000.geojson"
with open(geojson_path, "r") as f:
    geojson_data = json.load(f)

print("simulate_rice_grid_1000x1000.geojson loaded successfully.")

# Load All Districts GeoJSON Map Data
all_districts_geojson_path = "assets/five_punjab_districts.geojson"
with open(all_districts_geojson_path, "r") as f:
    all_districts_geojson = json.load(f)

print("five_punjab_districts.geojson loaded successfully.")

# API Endpoints

@app.route("/districts", methods=["GET"])
def get_districts():
    # Return unique districts from the dataset
    districts = historical_data["District"].unique().tolist()
    return jsonify({"districts": districts})

@app.route("/all-districts", methods=["GET"])
def get_all_districts():
    # Return GeoJSON for all districts
    return jsonify(all_districts_geojson)

@app.route("/district/<district_name>/historical", methods=["GET"])
def get_historical(district_name):
    # Filter historical data for the given district
    district_data = historical_data[historical_data["District"] == district_name]
    
    if district_data.empty:
        return jsonify({"error": "District not found"}), 404

    # Extract historical trends
    historical_trends = {
        "Years": district_data["Year"].tolist(),
        "Area": district_data["Area"].tolist(),
        "Production": district_data["Production"].tolist(),
        "Yield": district_data["Crop_Yield"].tolist()
    }
    return jsonify({"District": district_name, "Historical_Data": historical_trends})

@app.route("/district/<district_name>/predict", methods=["POST"])
def predict_production(district_name):
    # Simulate rice-producing area for now (this would be classified dynamically in production)
    rice_area = historical_data[historical_data["District"] == district_name]["Area"].mean()  # Use historical average area
    
    if pd.isna(rice_area):
        return jsonify({"error": "District not found"}), 404

    # Simulate weather inputs
    temperature = np.random.uniform(25, 35)  # Simulated temperature
    rainfall = np.random.uniform(100, 300)  # Simulated rainfall
    humidity = np.random.uniform(60, 90)  # Simulated humidity

    # Prepare input for the model
    inputs = np.array([[rice_area, temperature, rainfall, humidity]])
    predicted_yield = model.predict(inputs)[0]
    predicted_production = predicted_yield * rice_area

    return jsonify({
        "District": district_name,
        "Predicted_Production": round(predicted_production, 2),
        "Inputs": {
            "Area": round(rice_area, 2),
            "Temperature": round(temperature, 2),
            "Rainfall": round(rainfall, 2),
            "Humidity": round(humidity, 2)
        }
    })

@app.route("/district/<district_name>/map", methods=["GET"])
def get_district_map(district_name):
    # Filter GeoJSON data for the specified district
    district_features = [
        feature for feature in geojson_data["features"]
        if feature["properties"].get("district") == district_name
    ]
    if not district_features:
        return jsonify({"error": f"District '{district_name}' not found"}), 404
    return jsonify({"type": "FeatureCollection", "features": district_features})

if __name__ == "__main__":
    app.run(debug=True)
