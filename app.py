import streamlit as st
import feedparser
import requests
import time
from datetime import datetime, timezone, timedelta
import socket

socket.setdefaulttimeout(10)

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(layout="wide", page_title="GLOBAL NEWS INTELLIGENCE")

st.title("🌍 GLOBAL NEWS INTELLIGENCE ENGINE (STABLE)")

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

refresh_interval = st.slider("Refresh interval (seconds)", 15, 120, 30)
time_window = st.slider("Show news from last (minutes)", 60, 360, 180)

# -------------------------------------------------
# LIVE BADGE
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
# FEEDS (MAX COVERAGE)
# -------------------------------------------------
GOOGLE_FEEDS = [
    "https://news.google.com/rss/search?q=breaking+news",
    "https://news.google.com/rss/search?q=world+news",
    "https://news.google.com/rss/search?q=India",
    "https://news.google.com/rss/search?q=stock+market",
    "https://news.google.com/rss/search?q=business",
    "https://news.google.com/rss/search?q=technology",
]

TWITTER_RSS = [
    "https://nitter.net/search/rss?f=tweets&q=breaking+news",
    "https://nitter.net/search/rss?f=tweets&q=stock+market",
]

# -------------------------------------------------
# SAFE HELPERS
# -------------------------------------------------
def safe_feed(url):
    try:
        return feedparser.parse(url)
    except Exception:
        return None

def fetch_gdelt():
    try:
        r = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params={
                "query": "global",
                "mode": "artlist",
                "maxrecords": 50,
                "format": "json"
            },
            timeout=10
        )
        return r.json().get("articles", [])
    except Exception:
        return []

def is_recent(dt):
    return dt >= datetime.now(timezone.utc) - timedelta(minutes=time_window)

# -------------------------------------------------
# LIVE MODE
# -------------------------------------------------
if st.session_state.live:

    start = time.time()
    items = []

    with placeholder.container():

        st.subheader(f"Updated @ {datetime.utcnow().strftime('%H:%M:%S')} UTC")

        # ---------- GOOGLE NEWS ----------
        for url in GOOGLE_FEEDS:
            feed = safe_feed(url)
            if not feed:
                continue

            for e in feed.entries:
                try:
                    pub = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
                except:
                    continue

                if not is_recent(pub):
                    continue
                if e.link in st.session_state.seen:
                    continue

                items.append(("Google", pub, e.title, e.link))

        # ---------- GDELT ----------
        for art in fetch_gdelt():
            link = art.get("url")
            title = art.get("title", "GDELT Event")

            if not link or link in st.session_state.seen:
                continue

            items.append(("GDELT", datetime.now(timezone.utc), title, link))

        # ---------- TWITTER SIGNALS ----------
        for url in TWITTER_RSS:
            feed = safe_feed(url)
            if not feed:
                continue

            for e in feed.entries:
                if e.link in st.session_state.seen:
                    continue
                items.append(("X/Twitter", datetime.now(timezone.utc), e.title, e.link))

        # ---------- DISPLAY ----------
        items.sort(key=lambda x: x[1], reverse=True)

        if not items:
            st.warning("Feeds are temporarily quiet or blocked.")
        else:
            st.success(f"Showing {len(items)} live items")

        for src, pub, title, link in items[:100]:
            st.session_state.seen.add(link)
            st.markdown(f"### {title}")
            st.write(f"🕒 {pub.strftime('%Y-%m-%d %H:%M:%S')} | 📡 {src}")
            st.markdown(f"[Open]({link})")
            st.divider()

    remaining = max(refresh_interval - int(time.time() - start), 0)
    st.write(f"⏳ Next refresh in {remaining}s")
    time.sleep(remaining)
    st.rerun()

else:
    st.info("Click 🚀 Start Live to begin global aggregation.")
