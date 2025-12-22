import streamlit as st
import time
import feedparser
from datetime import datetime, timezone

st.set_page_config(layout="wide", page_title="LIVE NEWS TIMER TEST")

st.title("📰 LIVE NEWS TEST APP (WITH TIMER)")

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "live" not in st.session_state:
    st.session_state.live = False

# -------------------------------------------------
# BUTTONS
# -------------------------------------------------
col1, col2 = st.columns(2)

if col1.button("🚀 Start Live Updates"):
    st.session_state.live = True

if col2.button("🛑 Stop Live"):
    st.session_state.live = False

interval = st.slider("Refresh Interval (seconds)", 5, 30, 10)

st.write("Live Mode:", st.session_state.live)

placeholder = st.empty()

# -------------------------------------------------
# LIVE SOURCES
# -------------------------------------------------
LIVE_SOURCES = [
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "https://feeds.reuters.com/reuters/topNews"
]

# -------------------------------------------------
# HELPER: TIME AGO
# -------------------------------------------------
def time_ago(published_time):
    now = datetime.now(timezone.utc)
    diff = now - published_time

    seconds = int(diff.total_seconds())

    if seconds < 60:
        return f"{seconds} sec ago"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    if seconds < 86400:
        return f"{seconds // 3600} hr ago"
    return f"{seconds // 86400} day ago"

# -------------------------------------------------
# LIVE MODE
# -------------------------------------------------
if st.session_state.live:

    start_time = time.time()

    with placeholder.container():

        st.subheader(f"🔴 LIVE FEED (Updated @ {datetime.utcnow().strftime('%H:%M:%S')} UTC)")

        all_news = []

        for src in LIVE_SOURCES:
            feed = feedparser.parse(src)
            all_news.extend(feed.entries)

        for item in all_news[:10]:

            # published time
            try:
                pub_time = datetime(*item.published_parsed[:6], tzinfo=timezone.utc)
                ago = time_ago(pub_time)
            except:
                ago = "time unknown"

            st.markdown(f"### {item.title}")
            st.write(f"🕒 Published: **{ago}**")
            st.markdown(f"[Open Article]({item.link})")
            st.divider()

    # -------------------------------
    # COUNTDOWN TIMER
    # -------------------------------
    elapsed = int(time.time() - start_time)
    remaining = max(interval - elapsed, 0)

    st.write(f"⏳ Next refresh in **{remaining} seconds**")

    time.sleep(remaining)
    st.rerun()

else:
    st.info("Click 🚀 Start Live Updates to begin.")
