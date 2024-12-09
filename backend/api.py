from datetime import datetime, timedelta
from flask import jsonify, request
import os
import json
from crop_prediction import (
    get_districts_data,
    get_district_geojson,
    predict_yield,
    load_historical_data,
)
from trend_analysis import (
    fetch_news,
    process_articles,
    save_articles_and_insights,
    get_last_execution,
    update_last_execution,
)

print(f"Current working directory: {os.getcwd()}")
# Constants
NEWS_OUTPUT_DIR = "assets/news_insights"


# Load shared data
historical_data, geojson_data, all_districts_geojson = load_historical_data()


def register_routes(app):
    # District APIs (unchanged)
    @app.route("/districts", methods=["GET"])
    def get_districts():
        return jsonify({"districts": get_districts_data(historical_data)})

    @app.route("/all-districts", methods=["GET"])
    def get_all_districts():
        return jsonify(all_districts_geojson)

    @app.route("/district/<district_name>/historical", methods=["GET"])
    def get_historical(district_name):
        data = get_districts_data(historical_data, district_name)
        if not data:
            return jsonify({"error": "District not found"}), 404
        return jsonify(data)

    @app.route("/district/<district_name>/predict", methods=["POST"])
    def predict_production(district_name):
        prediction = predict_yield(historical_data, district_name)
        if not prediction:
            return jsonify({"error": "District not found"}), 404
        return jsonify(prediction)

    @app.route("/district/<district_name>/map", methods=["GET"])
    def get_district_map(district_name):
        geojson = get_district_geojson(geojson_data, district_name)
        if not geojson:
            return jsonify({"error": f"District '{district_name}' not found"}), 404
        return jsonify(geojson)

    # News APIs
    @app.route("/news/trigger", methods=["POST"])
    def trigger_news_processing():
        """
        Trigger news processing, allowing optional date specification.
        """
        date_param = request.args.get("date", None)

        # Default to yesterday if no date is provided
        date_to_process = (
            datetime.now() - timedelta(days=1) if not date_param else datetime.strptime(date_param, "%Y-%m-%d")
        )
        date_str = date_to_process.strftime("%Y-%m-%d")

        # Fetch and process news
        articles = fetch_news(date_to_process)
        processed_data = process_articles(articles)
        save_articles_and_insights(date_str, articles, processed_data, NEWS_OUTPUT_DIR)
        update_last_execution(date_str)

        return jsonify({
            "message": "News processing completed.",
            "insights_saved": date_str,
            "total_articles": processed_data["total_articles"],
            "relevant_articles": processed_data["relevant_articles_count"],
            "insights_count": processed_data["insights_count"]
        })




    @app.route("/news/insights/<date>", methods=["GET"])
    def get_news_insights(date):
        file_path = os.path.join(NEWS_OUTPUT_DIR, f"{date}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                results = json.load(f)
            return jsonify({"date": date, "results": results})
        return jsonify({"error": f"No insights available for {date}."}), 404

    @app.route("/news/dates", methods=["GET"])
    def get_available_dates():
        files = [f.split(".")[0] for f in os.listdir(NEWS_OUTPUT_DIR) if f.endswith(".json")]
        return jsonify({"available_dates": sorted(files)})
