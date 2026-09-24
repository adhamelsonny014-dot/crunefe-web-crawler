import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configure page
st.set_page_config(
    page_title="Web Crawler Dashboard",
    layout="wide",
    page_icon="🕷️"
)

# Title and description
st.title("🕷️ Intelligent Web Crawler Dashboard")
st.markdown("A dashboard to visualize crawlability score, extracted data, and crawling recommendations.")

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('reuters_news_extended.csv')
        return df
    except Exception as e:
        st.error("Error loading data. Make sure the CSV file exists.")
        st.exception(e)
        return pd.DataFrame()

df = load_data()

import json

def load_crawlability_score():
    try:
        with open("crawlability_score.json", "r") as f:
            data = json.load(f)
            return data.get("score", 0)
    except FileNotFoundError:
        st.warning("Crawlability score not found.")
        return 0

crawlability_score = load_crawlability_score()


# Display Raw Data
st.header("📦 Extracted News Articles Preview")
if not df.empty:
    st.dataframe(df[['title', 'url', 'time', 'image_url']])
else:
    st.warning("No data loaded yet.")

# Visualization: Number of Articles per Date
if not df.empty:
    st.header("📈 Article Distribution Over Time")

    # Convert time to datetime
    #df['date'] = pd.to_datetime(df['time']).dt.date
    df['date'] = pd.to_datetime(df['time'], utc=True, errors='coerce').dt.date


    # Count articles per day
    daily_counts = df['date'].value_counts().sort_index()

    fig, ax = plt.subplots()
    daily_counts.plot(kind='bar', ax=ax)
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Articles")
    ax.set_title("News Articles Published Over Time")
    st.pyplot(fig)

# Crawlability Score (Example)
st.header("🛡️ Crawlability Score")
crawlability_score = load_crawlability_score()
st.progress(crawlability_score)
st.write(f"Score: {crawlability_score}/100")

# Recommendations Section
st.header("💡 Recommendations")
st.markdown("""
- Use `robots.txt` parser to respect crawl rules.
- If JavaScript-heavy, use Playwright/Selenium.
- Store data in CSV or SQLite for better management.
- Schedule crawls using cron jobs or Airflow.
""")

# Team section
st.header("👥 Team Members")
st.markdown("""
- Omar – Dashboard & GitHub
- Lojy – Content Extractor
- Adham – crawlability specialist and js api handler
""")