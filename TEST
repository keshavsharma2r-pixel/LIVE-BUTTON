import streamlit as st
import time
import feedparser
from datetime import datetime

st.set_page_config(layout="wide", page_title="TEST LIVE BUTTON")

st.title("LIVE TEST")

if "live" not in st.session_state:
    st.session_state.live = False

col1, col2 = st.columns(2)

if col1.button("🚀 Start Live Updates"):
    st.session_state.live = True

if col2.button("🛑 Stop Live"):
    st.session_state.live = False

st.write("Live mode:", st.session_state.live)

interval = st.slider("Refresh Interval (sec)", 5, 30, 10)

placeholder = st.empty()

LIVE_SOURCES = [
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "https://feeds.reuters.com/reuters/topNews",
]

if st.session_state.live:

    with placeholder.container():

        st.write(f"🔴 LIVE FEED UPDATED @ {datetime.now().strftime('%H:%M:%S')}")
        all_news = []

        for src in LIVE_SOURCES:
            feed = feedparser.parse(src)
            all_news.extend(feed.entries)

        for item in all_news[:10]:
            st.write("###", item.title)
            st.markdown(f"[Open]({item.link})")
            st.divider()

    time.sleep(interval)
    st.experimental_rerun()

else:
    st.info("Click Start Live Updates to begin.")
