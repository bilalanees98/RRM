# to run: python app-v2.py
from flask import Flask, jsonify, request
import pandas as pd
import joblib
import numpy as np
import json
import os
import requests
from openai import OpenAI
from datetime import datetime

app = Flask(__name__)

# Paths for assets
historical_csv_path = "assets/simulated_crop_yield_with_weather_and_humidity.csv"
geojson_path = "assets/simulate_rice_grid_1000x1000.geojson"
all_districts_geojson_path = "assets/five_punjab_districts.geojson"
news_output_dir = "news_insights"
execution_log_file = "last_execution.json"

# Ensure output directory exists
os.makedirs(news_output_dir, exist_ok=True)

# Load historical data
historical_data = pd.read_csv(historical_csv_path)
historical_data["Year"] = historical_data["Year"].str.split("-").str[0].astype(int)

# Load trained model
model = joblib.load("assets/yield_prediction_model.pkl")

# Load GeoJSON data
with open(geojson_path, "r") as f:
    geojson_data = json.load(f)

with open(all_districts_geojson_path, "r") as f:
    all_districts_geojson = json.load(f)

# API Keys
NEWS_API_KEY = ""  # Replace with your NewsAPI key
OPENAI_API_KEY = ""
client = OpenAI(
  api_key=OPENAI_API_KEY,  # this is also the default, it can be omitted
)

# News source and keywords
local_sources = ["dawn.com", "business-recorder.com"]
global_sources = ["reuters.com", "bloomberg.com"]
keywords = ["rice", "agriculture", "export", "import", "crop yield", "food security"]

# Helper Functions

def fetch_news():
    """Fetch news articles from NewsAPI."""
    all_articles = []
    for source in local_sources + global_sources:
        for keyword in keywords:
            url = f"https://newsapi.org/v2/everything?q={keyword}&domains={source}&apiKey={NEWS_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                articles = response.json().get("articles", [])
                all_articles.extend(articles)
            else:
                print(f"Failed to fetch from {source} with keyword {keyword}.")
    return all_articles

def process_articles(articles):
    """
    Process articles to identify relevance and extract insights.
    Stores all articles with their title, URL, and relevancy status.
    Generates insights only for relevant articles.
    """
    processed_articles = []  # To store all articles with their relevance status
    insights = []  # To store insights for relevant articles

    for article in articles:
        title = article.get("title", "")
        url = article.get("url", "No URL")

        if not title:
            continue  # Skip articles without a title

        # Filter for relevance using GPT
        filter_prompt = (
            f"You are an expert in agricultural markets. Determine if the following headline is relevant to rice supply, demand, "
            f"or pricing. Respond with 'Relevant' or 'Irrelevant'.\n\nHeadline: {title}"
        )
        filter_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in agricultural markets."},
                {"role": "user", "content": filter_prompt},
            ]
        )
        print('filter_response: ', filter_response.choices[0].message.content.strip())
        relevance = filter_response.choices[0].message.content.strip()

        # Store article with relevancy status
        processed_articles.append({
            "title": title,
            "url": url,
            "relevancy": relevance
        })

        # If relevant, generate insights
        if relevance.lower() == "relevant":
            content = article.get("content", "")
            insight_prompt = (
                f"Summarize the key insights about rice supply, demand, and pricing from the following article. "
                f"Include potential implications and a link to the article.\n\n{content}"
            )
            insight_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in agricultural markets."},
                    {"role": "user", "content": insight_prompt},
                ]
            )
            print('insight_response: ', insight_response.choices[0].message.content.strip())
            insights.append({
                "title": title,
                "insight": insight_response.choices[0].message.content.strip(),
                "url": url
            })

    return processed_articles, insights


def save_articles_and_insights(date, articles, insights):
    """
    Save processed articles (with relevancy status) and relevant insights to a JSON file.
    """
    output_data = {
        "date": date,
        "articles": articles,  # Includes all articles with title, URL, and relevancy
        "insights": insights   # Includes detailed insights for relevant articles
    }
    output_file = os.path.join(news_output_dir, f"{date}.json")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)
    return output_file


def get_last_execution():
    """Retrieve the last execution date from the log."""
    if os.path.exists(execution_log_file):
        with open(execution_log_file, "r") as f:
            return json.load(f)
    return {}

def update_last_execution(date):
    """Update the log with the last execution date."""
    with open(execution_log_file, "w") as f:
        json.dump({"last_execution": date}, f)

# News API Endpoints

@app.route("/news/trigger", methods=["POST"])
def trigger_news_processing():
    """Trigger news processing, ensuring it runs only once per day."""
    override = True #request.args.get("override", "false").lower() == "true"
    today = datetime.now().strftime("%Y-%m-%d")

    # Check last execution date
    last_execution = get_last_execution().get("last_execution", None)
    if last_execution == today and not override:
        return jsonify({"error": "News processing has already been run today."}), 400

    # Fetch and process news
    articles = fetch_news()
    insights = process_articles(articles)
    save_articles_and_insights(today, articles,insights)
    update_last_execution(today)

    return jsonify({"message": "News processing completed.", "insights_saved": today})

@app.route("/news/insights/<date>", methods=["GET"])
def get_news_insights(date):
    """Retrieve stored insights for a specific date."""
    file_path = os.path.join(news_output_dir, f"{date}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            insights = json.load(f)
        return jsonify({"date": date, "insights": insights})
    else:
        return jsonify({"error": f"No insights available for {date}."}), 404

@app.route("/news/dates", methods=["GET"])
def get_available_dates():
    """Get a list of available dates for which insights exist."""
    files = [f.split(".")[0] for f in os.listdir(news_output_dir) if f.endswith(".json")]
    return jsonify({"available_dates": sorted(files)})

# Existing District and Prediction Endpoints
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
