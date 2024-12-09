import os
import json
import requests
from openai import OpenAI
from datetime import datetime, timedelta

# News API Key - personal
# News API Key - work
NEWS_API_KEY = "INSERT KEY HERE"
OPENAI_API_KEY = "INSERT KEY HERE"

client = OpenAI(api_key=OPENAI_API_KEY)

# Execution log file to track the last execution date
execution_log_file = "assets/last_execution.json"

def fetch_news(date=None):
    """
    Fetch news articles from NewsAPI with optimized API calls for a specific date.
    If no date is provided, default to yesterday.
    """
    sources = ",".join([
        "ary-news", "al-jazeera-english", "bloomberg", "reuters",
        "business-insider", "google-news", "the-times-of-india"
    ])

    # Pre-defined keywords for the query
    query = (
        "+rice AND (\"production\" OR \"yield\" OR \"trade\" OR \"price\" OR \"flood\" OR \"policy\") "
        "OR \"global rice trade\" "
        "OR \"Indian rice exports\" "
        "OR \"Pakistan rice industry\" "
        "OR \"food inflation\" "
        "OR \"climate change AND rice\""
    )

    # Use provided date or default to yesterday
    target_date = date if date else datetime.now() - timedelta(days=1)
    target_date_str = target_date.strftime('%Y-%m-%d')

    # Define the API request
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&"
        f"sources={sources}&"
        f"from={target_date_str}&"
        f"to={target_date_str}&"
        f"sortBy=publishedAt&"
        f"pageSize=100&"  # Maximize results per call
        f"apiKey={NEWS_API_KEY}"
    )

    # Make the API call
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get("articles", [])
        print(f"Fetched {len(articles)} articles from NewsAPI for {target_date_str}.")
        return articles
    else:
        print(f"Failed to fetch news. Status Code: {response.status_code}, Response: {response.text}")
        return []

def process_articles(articles):
    """
    Process articles to identify relevance, extract insights, and generate a TL;DR.
    Generates a TL;DR for all relevant insights.
    """
    processed_articles = []  # All articles with relevance status
    relevant_insights = []  # Insights for relevant articles
    tldr_points = []  # Bullet points for the TL;DR

    # 1st Prompt: Filter articles based on headlines
    for article in articles:
        title = article.get("title", "")
        url = article.get("url", "No URL")
        content = article.get("content", "")

        if not title:
            continue  # Skip articles without a title

        filter_prompt = (
            f"You are a Pakistani expert in local and global agricultural markets. Determine if the following headline is relevant to rice supply, demand, "
            f"or pricing. Respond with 'Relevant' or 'Irrelevant'.\n\nHeadline: {title}"
        )
        filter_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Pakistani expert in agricultural markets."},
                {"role": "user", "content": filter_prompt},
            ]
        )
        relevance = filter_response.choices[0].message.content.strip()

        # Store article with relevance status
        processed_articles.append({
            "title": title,
            "url": url,
            "relevancy": relevance
        })

        # 2nd Prompt: Insights for relevant articles
        if relevance.lower() == "relevant":
            insights_prompt = (
                f"Analyse the following article to identify potential implications on Rashid Rice Mills on rice supply, "
                f"demand and price globally and locally. Your response should be to the point and in one paragraph of no more than "
                f"200 words. Your analysis will be used by executives at Rashid Rice Mills to make decisions around purchase of more "
                f"raw materials and increasing or decreasing production. Take special note that you cannot mention anything about "
                f"changing the product.\n\n{content}"
            )
            insights_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a Pakistani expert in agricultural markets. You help decision makers at Rashid Rice Mills in Pakistan. "
                            "Rashid Rice Mills purchases rice paddy from different districts in Pakistan, processes it to produce rice. "
                            "This rice is sold to local distributors and exported to markets in UAE and Saudi Arabia. Your goal is to "
                            "analyze news from different sources and identify key insights and implications about rice supply, demand, and pricing."
                            "If no insights have been provided to you return a blank response."
                        )
                    },
                    {"role": "user", "content": insights_prompt},
                ]
            )
            insight_text = insights_response.choices[0].message.content.strip()

            relevant_insights.append({
                "title": title,
                "insight": insight_text,
                "url": url
            })

    # 3rd Prompt: Generate TL;DR
    tldr_prompt = (
        "Combine the following insights into a concise, high-level summary (TL;DR) that can be read in 30 seconds. "
        "Focus on key takeaways and potential implications for Rashid Rice Mills."
        "If you are not provided any insights return a blank response.\n\n" + 
        "\n".join([insight['insight'] for insight in relevant_insights])
    )
    tldr_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert in summarizing insights for executives at Rashid Rice Mills."},
            {"role": "user", "content": tldr_prompt},
        ]
    )
    tldr_points = tldr_response.choices[0].message.content.strip().split("\n")

    return {
        "total_articles": len(articles),
        "relevant_articles_count": len(relevant_insights),
        "insights_count": len(relevant_insights),
        "tldr_points": tldr_points,
        "relevant_insights": relevant_insights
    }




def save_articles_and_insights(date, articles, processed_data, NEWS_OUTPUT_DIR):
    """
    Save processed articles, insights, and TL;DR to a JSON file.
    """
    output_data = {
        "date": date,
        "total_articles": processed_data["total_articles"],
        "relevant_articles_count": processed_data["relevant_articles_count"],
        "insights_count": processed_data["insights_count"],
        "tldr": processed_data["tldr_points"],
        "insights": processed_data["relevant_insights"]
    }
    output_file = os.path.join(NEWS_OUTPUT_DIR, f"{date}.json")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)
    return output_file




def get_last_execution():
    """
    Retrieve the last execution date from the log.
    """
    if os.path.exists(execution_log_file):
        with open(execution_log_file, "r") as f:
            return json.load(f)
    return {}


def update_last_execution(date):
    """
    Update the log with the last execution date.
    """
    with open(execution_log_file, "w") as f:
        json.dump({"last_execution": date}, f)

############## Manual processing #######################

def process_manual_articles(input_file, output_dir):
    """
    Process articles from a manually provided JSON file, generating insights and TL;DR summaries.
    Save results grouped by date in separate JSON files.
    """
    try:
        # Load the input JSON file
        with open(input_file, "r") as f:
            data = json.load(f)
            articles = data.get("articles", [])
        
        if not articles:
            print("No articles found in the input JSON.")
            return

        # Group articles by date
        articles_by_date = {}
        for article in articles:
            date = article.get("date")
            if date:
                if date not in articles_by_date:
                    articles_by_date[date] = []
                articles_by_date[date].append(article)

        # Process articles for each date
        for date, articles in articles_by_date.items():
            print(f"Processing articles for date: {date}")
            processed_data = process_articles(articles)  # Reuse the process_articles function
            save_articles_and_insights(date, articles, processed_data, output_dir)

        print(f"Processing complete. Results saved in {output_dir}.")
    except Exception as e:
        print(f"Error processing manual articles: {e}")
