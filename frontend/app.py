# app.py
# to run: streamlit run app.py
import streamlit as st
from supply import display_supply_section
from trends import display_trends_section

# Generic Title
st.header("Insights Dashboard")

# Initialize session state for section
if "section" not in st.session_state:
    st.session_state.section = "Supply"

# Sidebar Navigation with Buttons
st.sidebar.title("Navigation")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Supply"):
        st.session_state.section = "Supply"
with col2:
    if st.button("Trends"):
        st.session_state.section = "Trends"

# Display the selected section
if st.session_state.section == "Supply":
    display_supply_section()
elif st.session_state.section == "Trends":
    display_trends_section()
