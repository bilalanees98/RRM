# trends.py
import streamlit as st
import requests
from datetime import datetime

# Backend API URL
API_URL = "http://127.0.0.1:5000"

def display_trends_section():
    """
    Display the Trends section of the application.
    """
    st.markdown("### Trends: News Insights")

    # Fetch available dates
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

    # Allow the user to specify a date for processing
    date = st.date_input("Select a date for processing news insights", datetime.now().date())
    if st.button("Run News Insights Processing"):
        try:
            response = requests.post(f"{API_URL}/news/trigger?date={date}")
            if response.status_code == 200:
                st.success(f"News insights processing triggered successfully for {date}.")
            else:
                st.error(response.json().get("error", "Failed to trigger the news insights processing."))
        except requests.exceptions.RequestException:
            st.error("Backend not reachable for triggering news insights.")

    # Dropdown to select a date
    if available_dates:
        selected_date = st.selectbox("Select a Date", sorted(available_dates, reverse=True))
        if st.button("Fetch Insights"):
            try:
                response = requests.get(f"{API_URL}/news/insights/{selected_date}")
                if response.status_code == 200:
                    results = response.json().get("results",[])
                    articles_analyzed = results.get("total_articles", 0)
                    relevant_articles_count = results.get("relevant_articles_count", 0)
                    insights_count = results.get("insights_count", 0)
                    tldr_points = results.get("tldr", [])
                    insights = results.get("insights", [])

                    # Display Metrics
                    st.markdown(f"**Total Articles Fetched for the Day:** {articles_analyzed}")
                    st.markdown(f"**Total Articles Filtered for Relevancy:** {relevant_articles_count}")
                    st.markdown(f"**Total Relevant Articles with Insights:** {insights_count}")

                    # TL;DR Section
                    if tldr_points:
                        st.markdown("### TL;DR")
                        for point in tldr_points:
                            st.write(point)

                    # Detailed Insights Section
                    if insights:
                        st.markdown("### Article Summaries")
                        for insight in insights:
                            st.markdown(f"#### {insight['title']}")
                            st.write(insight["insight"])
                            st.write(f"[Source]({insight['url']})")
                    else:
                        st.info("No insights available for the selected date.")
                else:
                    st.error(f"No insights available for {selected_date}.")
            except requests.exceptions.RequestException:
                st.error("Backend not reachable for fetching insights.")
    else:
        st.info("No insights available. Run the news insights processing first.")
