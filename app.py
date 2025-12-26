import streamlit as st
import feedparser
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import socket, urllib.parse

# ------------------ TIMEZONE ------------------
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")
socket.setdefaulttimeout(10)

# ------------------ CONFIG ------------------
st.set_page_config(layout="wide", page_title="News Intelligence Terminal")
st.title("📰 News Intelligence Terminal (IST – New Delhi)")

# ------------------ SESSION ------------------
if "live" not in st.session_state:
    st.session_state.live = False
if "seen" not in st.session_state:
    st.session_state.seen = set()
if "last_fetch" not in st.session_state:
    st.session_state.last_fetch = None
if "last_update" not in st.session_state:
    st.session_state.last_update = None
if "new_count" not in st.session_state:
    st.session_state.new_count = 0

# ------------------ CONTROLS ------------------
c1, c2 = st.columns(2)

if c1.button("🚀 Start Live"):
    st.session_state.live = True
    st.session_state.seen.clear()
    st.session_state.last_fetch = None
    st.session_state.last_update = datetime.now(IST)

if c2.button("🛑 Stop"):
    st.session_state.live = False

window = st.slider("Show news from last (minutes)", 60, 360, 180)

# ------------------ STATUS ------------------
if st.session_state.live:
    st.markdown(
        "<div style='color:white;background:red;padding:6px 12px;"
        "border-radius:6px;font-weight:bold;'>🔴 LIVE</div>",
        unsafe_allow_html=True
    )
    st.caption("Checking for updates…")
else:
    st.info("Live mode OFF")

# ------------------ SAFE FEED ------------------
def fetch_feed(url):
    try:
        return feedparser.parse(url)
    except:
        return None

# ------------------ HELPERS ------------------
def is_recent(dt_utc):
    return dt_utc.astimezone(IST) >= datetime.now(IST) - timedelta(minutes=window)

def get_source(entry):
    if hasattr(entry, "source") and hasattr(entry.source, "title"):
        return entry.source.title
    try:
        return urllib.parse.urlparse(entry.link).netloc.replace("www.", "").upper()
    except:
        return "UNKNOWN"

# ------------------ EXPANDED SOURCES ------------------

# Google News (massive aggregation)
GOOGLE_QUERIES = [
    "breaking news",
    "world news",
    "global markets",
    "stock market",
    "business news",
    "technology news",
    "earnings results",
    "merger acquisition",
    "IPO market",
    "central bank policy",
    "inflation interest rates",
    "geopolitics conflict",
    "oil prices",
    "currency markets",
]

GOOGLE_FEEDS = [
    f"https://news.google.com/rss/search?q={urllib.parse.quote_plus(q)}"
    for q in GOOGLE_QUERIES
]

# Tier-1 global financial media
TIER1_GLOBAL = [
    "https://www.reuters.com/rssFeed/worldNews",
    "https://www.reuters.com/rssFeed/businessNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
]

# India general & economy
INDIA_FEEDS = [
    "https://news.google.com/rss/search?q=India+breaking+news",
    "https://news.google.com/rss/search?q=India+economy",
    "https://news.google.com/rss/search?q=India+stock+market",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
]

# Markets (global + India, unified)
MARKET_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://www.livemint.com/rss/markets",
    "https://www.business-standard.com/rss/markets-106.rss",
]

GLOBAL_FEEDS = GOOGLE_FEEDS + TIER1_GLOBAL

# ------------------ TABS ------------------
tab_global, tab_india, tab_market = st.tabs(
    ["🌍 Global", "🇮🇳 India", "📈 Markets"]
)

# ------------------ HYBRID RENDER ------------------
def render_news(feeds):
    FETCH_INTERVAL = 60  # seconds (HYBRID SAFE LIMIT)
    now = datetime.now(IST)

    if st.session_state.last_fetch:
        if (now - st.session_state.last_fetch).total_seconds() < FETCH_INTERVAL:
            return

    st.session_state.last_fetch = now
    new_items = 0
    collected = []

    for url in feeds:
        feed = fetch_feed(url)
        if not feed:
            continue

        for e in feed.entries:
            try:
                pub_utc = datetime(*e.published_parsed[:6], tzinfo=UTC)
            except:
                continue

            if not is_recent(pub_utc):
                continue

            if e.link in st.session_state.seen:
                continue

            st.session_state.seen.add(e.link)
            new_items += 1

            collected.append((
                pub_utc.astimezone(IST),
                e.title,
                e.link,
                get_source(e)
            ))

    if new_items > 0:
        st.session_state.last_update = now
        st.session_state.new_count = new_items

    collected.sort(key=lambda x: x[0], reverse=True)

    if not collected:
        st.warning("No new headlines in this interval.")
        return

    for pub, title, link, source in collected[:40]:
        st.markdown(f"### 🆕 {title}")
        st.write(f"🕒 {pub.strftime('%d %b %Y, %I:%M %p IST')}")
        st.markdown(
            f"<span style='background:#e5e7eb;padding:4px 8px;"
            f"border-radius:6px;font-size:12px;font-weight:600;'>"
            f"📰 {source}</span>",
            unsafe_allow_html=True
        )
        st.markdown(f"[Open Article]({link})")
        st.divider()

# ------------------ TAB CONTENT ------------------
with tab_global:
    if st.session_state.live:
        render_news(GLOBAL_FEEDS)
    else:
        st.info("Start live to see global news")

with tab_india:
    if st.session_state.live:
        render_news(INDIA_FEEDS)
    else:
        st.info("Start live to see India news")

with tab_market:
    if st.session_state.live:
        render_news(MARKET_FEEDS)
    else:
        st.info("Start live to see market news")

# ------------------ FOOTER ------------------
if st.session_state.last_update:
    st.success(
        f"🆕 {st.session_state.new_count} new headlines | "
        f"Last Update: {st.session_state.last_update.strftime('%d %b %Y, %I:%M %p IST')}"
    )
