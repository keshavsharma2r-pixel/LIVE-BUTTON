import streamlit as st
import time
import feedparser
from datetime import datetime, timezone, timedelta

st.set_page_config(layout="wide", page_title="LIVE LATEST NEWS ONLY")

st.title("📰 LIVE LATEST NEWS (NO OLD NEWS)")

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "live" not in st.session_state:
    st.session_state.live = False

if "seen_links" not in st.session_state:
    st.session_state.seen_links = set()

if "last_check" not in st.session_state:
    # start by allowing last 10 minutes
    st.session_state.last_check = datetime.now(timezone.utc) - timedelta(minutes=10)

# -------------------------------------------------
# CONTROLS
# -------------------------------------------------
col1, col2 = st.columns(2)

if col1.button("🚀 Start Live Updates"):
    st.session_state.live = True

if col2.button("🛑 Stop Live"):
    st.session_state.live = False

refresh_interval = st.slider("Refresh Interval (seconds)", 5, 30, 10)
latest_minutes = st.slider("Show news from last (minutes)", 1, 30, 5)

placeholder = st.empty()

# -------------------------------------------------
# LIVE SOURCES
# -------------------------------------------------
LIVE_SOURCES = [
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "https://feeds.reuters.com/reuters/topNews"
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
    return f"{seconds // 3600}h ago"

# -------------------------------------------------
# LIVE MODE
# -------------------------------------------------
if st.session_state.live:

    start_time = time.time()

    with placeholder.container():

        st.subheader(f"🔴 LIVE FEED — latest only (updated {datetime.utcnow().strftime('%H:%M:%S')} UTC)")

        fresh_news = []

        for src in LIVE_SOURCES:
            feed = feedparser.parse(src)

            for item in feed.entries:

                # published time check
                try:
                    pub_time = datetime(*item.published_parsed[:6], tzinfo=timezone.utc)
                except:
                    continue

                # 1️⃣ only latest X minutes
                if pub_time < datetime.now(timezone.utc) - timedelta(minutes=latest_minutes):
                    continue

                # 2️⃣ only new since last refresh
                if pub_time <= st.session_state.last_check:
                    continue

                # 3️⃣ no duplicates
                if item.link in st.session_state.seen_links:
                    continue

                fresh_news.append((pub_time, item))

        # sort newest first
        fresh_news.sort(key=lambda x: x[0], reverse=True)

        if not fresh_news:
            st.info("No NEW breaking news in this interval.")

        for pub_time, item in fresh_news:

            st.session_state.seen_links.add(item.link)

            st.markdown(f"### {item.title}")
            st.write(f"🕒 {time_ago(pub_time)}")
            st.markdown(f"[Open Article]({item.link})")
            st.divider()

        # update last check time
        st.session_state.last_check = datetime.now(timezone.utc)

    # countdown + rerun
    elapsed = int(time.time() - start_time)
    remaining = max(refresh_interval - elapsed, 0)

    st.write(f"⏳ Next refresh in **{remaining}s**")

    time.sleep(remaining)
    st.rerun()

else:
    st.info("Click 🚀 Start Live Updates to begin.")
