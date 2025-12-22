import streamlit as st
import time
import feedparser
from datetime import datetime

st.set_page_config(layout="wide", page_title="TEST LIVE BUTTON")

st.title("LIVE BUTTON TEST APP")

# ----------------------------------------------------------
# SESSION STATE — this keeps track of live mode
# ----------------------------------------------------------
if "live" not in st.session_state:
    st.session_state.live = False

# ----------------------------------------------------------
# BUTTONS
# ----------------------------------------------------------
col1, col2 = st.columns(2)

if col1.button("🚀 Start Live Updates"):
    st.session_state.live = True

if col2.button("🛑 Stop Live"):
    st.session_state.live = False

st.write("Live Mode:", st.session_state.live)

interval = st.slider("Refresh Interval (seconds)", 5, 30, 10)

placeholder = st.empty()

# ----------------------------------------------------------
# LIVE SOURCES
# ----------------------------------------------------------
LIVE_SOURCES = [
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "https://feeds.reuters.com/reuters/topNews"
]

# ----------------------------------------------------------
# LIVE MODE ACTIVE
# ----------------------------------------------------------
if st.session_state.live:

    with placeholder.container():

        st.write(f"🔴 LIVE FEED — Updated @ {datetime.now().strftime('%H:%M:%S')}")
        
        all_news = []

        for src in LIVE_SOURCES:
            feed = feedparser.parse(src)
            all_news.extend(feed.entries)

        # show some news
        for item in all_news[:10]:
            st.write("###", item.title)
            st.markdown(f"[Open]({item.link})")
            st.divider()

    # wait & rerun
    time.sleep(interval)
    st.rerun()

# ----------------------------------------------------------
# LIVE MODE OFF
# ----------------------------------------------------------
else:
    st.info("Click 🚀 Start Live Updates to begin.")
