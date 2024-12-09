from flask import Flask
from api import register_routes
from trend_analysis import (
    process_manual_articles
)
app = Flask(__name__)

# Register all routes
register_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
    # input_file = "assets/articles.json"
    # output_dir = "assets/news_insights"
    # process_manual_articles(input_file, output_dir)
