import streamlit as st
import time
import feedparser
from datetime import datetime, timezone, timedelta

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(layout="wide", page_title="🇮🇳 LIVE INDIA NEWS")

st.title("🇮🇳 LIVE INDIA NEWS (GENERAL + MARKET + NSE/BSE)")

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "live" not in st.session_state:
    st.session_state.live = False

if "seen_links" not in st.session_state:
    st.session_state.seen_links = set()

if "last_check" not in st.session_state:
    st.session_state.last_check = datetime.now(timezone.utc) - timedelta(minutes=30)

# -------------------------------------------------
# TOP CONTROLS
# -------------------------------------------------
news_type = st.radio(
    "Select News Category",
    ["🇮🇳 India – General", "📈 India – Market"],
    horizontal=True
)

col1, col2 = st.columns(2)

if col1.button("🚀 Start Live Updates"):
    st.session_state.live = True

if col2.button("🛑 Stop Live"):
    st.session_state.live = False

refresh_interval = st.slider("Refresh Interval (seconds)", 5, 30, 10)
latest_minutes = st.slider("Consider news from last (minutes)", 5, 60, 20)

# -------------------------------------------------
# FLASHING LIVE BADGE
# -------------------------------------------------
if st.session_state.live:
    badge_text = "🔴 LIVE INDIA" if "General" in news_type else "🔴 LIVE MARKET"
    st.markdown(
        f"""
        <style>
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
            100% {{ opacity: 1; }}
        }}
        .live-badge {{
            color: white;
            background: red;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: bold;
            display: inline-block;
            animation: pulse 1s infinite;
        }}
        </style>
        <div class="live-badge">{badge_text}</div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown("⚪ LIVE OFF")

placeholder = st.empty()

# -------------------------------------------------
# 🇮🇳 SOURCES
# -------------------------------------------------
INDIA_GENERAL_SOURCES = [
    "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
    "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
]

NSE_SOURCES = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://news.google.com/rss/search?q=NSE+India+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
]

BSE_SOURCES = [
    "https://www.livemint.com/rss/markets",
    "https://news.google.com/rss/search?q=BSE+Sensex+India+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
]

# -------------------------------------------------
# HELPER
# -------------------------------------------------
def time_ago(published_time):
    now = datetime.now(timezone.utc)
    diff = now - published_time
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"

# -------------------------------------------------
# LIVE MODE
# -------------------------------------------------
if st.session_state.live:

    start_time = time.time()

    with placeholder.container():

        st.subheader(f"Updated @ {datetime.utcnow().strftime('%H:%M:%S')} UTC")

        # -----------------------------
        # GENERAL NEWS
        # -----------------------------
        if "General" in news_type:
            active_sources = INDIA_GENERAL_SOURCES

        # -----------------------------
        # MARKET NEWS WITH NSE/BSE TABS
        # -----------------------------
        else:
            tab_nse, tab_bse = st.tabs(["📊 NSE", "🏦 BSE"])

        # -----------------------------
        # FUNCTION TO PROCESS FEEDS
        # -----------------------------
        def process_sources(sources):
            fresh = []

            for src in sources:
                feed = feedparser.parse(src)

                for item in feed.entries:
                    try:
                        pub_time = datetime(
                            *item.published_parsed[:6], tzinfo=timezone.utc
                        )
                    except:
                        continue

                    if pub_time < datetime.now(timezone.utc) - timedelta(minutes=latest_minutes):
                        continue

                    if pub_time <= st.session_state.last_check:
                        continue

                    if item.link in st.session_state.seen_links:
                        continue

                    fresh.append((pub_time, item))

            fresh.sort(key=lambda x: x[0], reverse=True)
            return fresh

        # -----------------------------
        # DISPLAY GENERAL
        # -----------------------------
        if "General" in news_type:
            fresh_news = process_sources(INDIA_GENERAL_SOURCES)

            if fresh_news:
                st.success(f"🔥 {len(fresh_news)} NEW updates")

                for pub_time, item in fresh_news:
                    st.session_state.seen_links.add(item.link)
                    st.markdown(f"### {item.title}")
                    st.write(f"🕒 {time_ago(pub_time)}")
                    st.markdown(f"[Open Article]({item.link})")
                    st.divider()

                st.session_state.last_check = datetime.now(timezone.utc)

            else:
                st.warning("No NEW breaking news. Showing latest headlines.")
                for src in INDIA_GENERAL_SOURCES:
