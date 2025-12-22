import streamlit as st
import feedparser
import requests
import time
from datetime import datetime, timezone, timedelta
import urllib.parse

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(layout="wide", page_title="GLOBAL NEWS INTELLIGENCE")

st.title("🌍 GLOBAL NEWS INTELLIGENCE ENGINE")

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "live" not in st.session_state:
    st.session_state.live = False

if "seen" not in st.session_state:
    st.session_state.seen = set()

# -------------------------------------------------
# CONTROLS
# -------------------------------------------------
col1, col2 = st.columns(2)

if col1.button("🚀 Start Live"):
    st.session_state.live = True

if col2.button("🛑 Stop"):
    st.session_state.live = False

refresh_interval = st.slider("Refresh interval (seconds)", 10, 60, 20)
time_window = st.slider("Show news from last (minutes)", 30, 240, 120)

# -------------------------------------------------
# FLASHING LIVE BADGE
# -------------------------------------------------
if st.session_state.live:
    st.markdown(
        """
        <style>
        @keyframes pulse { 0%{opacity:1;} 50%{opacity:.3;} 100%{opacity:1;} }
        .live { background:red;color:white;padding:6px 12px;
                border-radius:6px;font-weight:bold;animation:pulse 1s infinite; }
        </style>
        <div class="live">🔴 LIVE</div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown("⚪ LIVE OFF")

placeholder = st.empty()

# -------------------------------------------------
# SOURCE 1: GOOGLE NEWS SEARCH (MAX COVERAGE)
# -------------------------------------------------
GOOGLE_SEARCH_FEEDS = [
    "https://news.google.com/rss/search?q=breaking+news",
    "https://news.google.com/rss/search?q=world+news",
    "https://news.google.com/rss/search?q=India",
    "https://news.google.com/rss/search?q=stock+market",
    "https://news.google.com/rss/search?q=business",
    "https://news.google.com/rss/search?q=technology",
]

# -------------------------------------------------
# SOURCE 2: GDELT (GLOBAL EVENTS DATA)
# -------------------------------------------------
def fetch_gdelt():
    url = "https://api.gdeltproject.org/api/v2/doc/doc?query=global&mode=artlist&maxrecords=50&format=json"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return data.get("articles", [])
    except:
        return []

# -------------------------------------------------
# SOURCE 3: TWITTER SIGNALS (NITTER RSS)
# -------------------------------------------------
TWITTER_RSS = [
    "https://nitter.net/search/rss?f=tweets&q=breaking+news",
    "https://nitter.net/search/rss?f=tweets&q=stock+market",
    "https://nitter.net/search/rss?f=tweets&q=India+news",
]

# -------------------------------------------------
# HELPER
# -------------------------------------------------
def is_recent(published):
    return published >= datetime.now(timezone.utc) - timedelta(minutes=time_window)

# -------------------------------------------------
# LIVE MODE
# -------------------------------------------------
if st.session_state.live:

    start = time.time()

    with placeholder.container():

        st.subheader(f"Updated @ {datetime.utcnow().strftime('%H:%M:%S')} UTC")

        news_items = []

        # -------- GOOGLE NEWS --------
        for url in GOOGLE_SEARCH_FEEDS:
            feed = feedparser.parse(url)
            for item in feed.entries:
                try:
                    pub = datetime(*item.published_parsed[:6], tzinfo=timezone.utc)
                except:
                    continue
                if not is_recent(pub):
                    continue
                if item.link in st.session_state.seen:
                    continue
                news_items.append(("Google", pub, item.title, item.link))

        # -------- GDELT --------
        for art in fetch_gdelt():
            link = art.get("url")
            title = art.get("title", "GDELT Event")
            if link and link not in st.session_state.seen:
                news_items.append(("GDELT", datetime.now(timezone.utc), title, link))

        # -------- TWITTER SIGNALS --------
        for url in TWITTER_RSS:
            feed = feedparser.parse(url)
            for item in feed.entries:
                if item.link in st.session_state.seen:
                    continue
                news_items.append(("X/Twitter", datetime.now(timezone.utc), item.title, item.link))

        # -------- SORT & DISPLAY --------
        news_items.sort(key=lambda x: x[1], reverse=True)

        if not news_items:
            st.warning("No new data in this cycle — feeds are quiet.")
        else:
            st.success(f"Showing {len(news_items)} live items")

        for source, pub, title, link in news_items[:100]:
            st.session_state.seen.add(link)
            st.markdown(f"### {title}")
            st.write(f"🕒 {pub.strftime('%Y-%m-%d %H:%M:%S')} | 📡 {source}")
            st.markdown(f"[Open]({link})")
            st.divider()

    remaining = max(refresh_interval - int(time.time() - start), 0)
    st.write(f"⏳ Next refresh in {remaining}s")
    time.sleep(remaining)
    st.rerun()

else:
    st.info("Click 🚀 Start Live to begin global aggregation.")
