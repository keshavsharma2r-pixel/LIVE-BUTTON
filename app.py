import streamlit as st
import feedparser
from datetime import datetime, date
from zoneinfo import ZoneInfo
import socket, urllib.parse

# ------------------ TIMEZONE ------------------
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")
socket.setdefaulttimeout(10)

# ------------------ PAGE CONFIG ------------------
st.set_page_config(layout="wide", page_title="NEWS")
st.title("📰 NEWS")

# ------------------ SESSION STATE ------------------
if "live" not in st.session_state:
    st.session_state.live = False
if "seen" not in st.session_state:
    st.session_state.seen = set()
if "last_fetch" not in st.session_state:
    st.session_state.last_fetch = None

# Filter state
if "apply_filters" not in st.session_state:
    st.session_state.apply_filters = False
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "filter_date" not in st.session_state:
    st.session_state.filter_date = None
if "status_msg" not in st.session_state:
    st.session_state.status_msg = "Showing all news"

# ------------------ TOP RIGHT CONTROLS ------------------
left, right = st.columns([6, 2])

with right:
    if st.button("🔴 LIVE"):
        st.session_state.live = True
        st.session_state.seen.clear()
        st.session_state.last_fetch = None

    if st.button("⏹ STOP"):
        st.session_state.live = False

# ------------------ FILTER CONTROLS ------------------
st.divider()

f1, f2, f3, f4 = st.columns([5, 2, 1.5, 1.5])

with f1:
    search_input = st.text_input(
        "🔍 Global Search (company, topic, keyword)",
        placeholder="Reliance, FED, AI, war, inflation...",
        value=st.session_state.search_query
    )

with f2:
    date_input = st.date_input(
        "📅 Jump to date",
        value=st.session_state.filter_date or date.today()
    )

with f3:
    if st.button("🔍 Search"):
        st.session_state.search_query = search_input.strip()
        st.session_state.filter_date = date_input
        st.session_state.apply_filters = True
        st.session_state.seen.clear()

        if st.session_state.search_query:
            st.session_state.status_msg = (
                f'Showing results for "{st.session_state.search_query}" '
                f'on {st.session_state.filter_date.strftime("%d %b %Y")}'
            )
        else:
            st.session_state.status_msg = (
                f'Showing news for {st.session_state.filter_date.strftime("%d %b %Y")}'
            )

with f4:
    if st.button("🔄 Reset"):
        st.session_state.apply_filters = False
        st.session_state.search_query = ""
        st.session_state.filter_date = None
        st.session_state.seen.clear()
        st.session_state.status_msg = "Filters cleared — showing all news"

# ------------------ STATUS BANNERS ------------------
st.caption(st.session_state.status_msg)

if st.session_state.live:
    st.markdown(
        "<div style='background:red;color:white;padding:6px 10px;"
        "border-radius:6px;font-weight:bold;width:max-content;'>🔴 LIVE</div>",
        unsafe_allow_html=True
    )
else:
    st.info("Live mode OFF")

# ------------------ FEED UTILS ------------------
def fetch_feed(url):
    try:
        return feedparser.parse(url)
    except:
        return None

def get_source(entry):
    try:
        return urllib.parse.urlparse(entry.link).netloc.replace("www.", "").upper()
    except:
        return "UNKNOWN"

# ------------------ SOURCES ------------------
GLOBAL_FEEDS = [
    "https://news.google.com/rss",
    "https://www.reuters.com/rssFeed/worldNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
]

INDIA_FEEDS = [
    "https://news.google.com/rss/search?q=India",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
]

MARKET_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://www.livemint.com/rss/markets",
]

# ------------------ TABS ------------------
tab_global, tab_india, tab_market = st.tabs(
    ["🌍 Global", "🇮🇳 India", "📈 Markets"]
)

# ------------------ RENDER NEWS ------------------
def render_news(feeds):
    FETCH_INTERVAL = 60
    now = datetime.now(IST)

    if st.session_state.live:
        if st.session_state.last_fetch:
            if (now - st.session_state.last_fetch).total_seconds() < FETCH_INTERVAL:
                return
        st.session_state.last_fetch = now

    items = []

    for url in feeds:
        feed = fetch_feed(url)
        if not feed:
            continue

        for e in feed.entries:
            try:
                pub_utc = datetime(*e.published_parsed[:6], tzinfo=UTC)
                pub_ist = pub_utc.astimezone(IST)
            except:
                continue

            # Apply filters ONLY if Search clicked
            if st.session_state.apply_filters:
                if st.session_state.filter_date:
                    if pub_ist.date() != st.session_state.filter_date:
                        continue

                if st.session_state.search_query:
                    text = f"{e.title} {getattr(e,'summary','')}".lower()
                    if st.session_state.search_query.lower() not in text:
                        continue

            if e.link in st.session_state.seen:
                continue

            st.session_state.seen.add(e.link)
            items.append((pub_ist, e.title, e.link, get_source(e)))

    items.sort(key=lambda x: x[0], reverse=True)

    if not items:
        if st.session_state.apply_filters:
            st.warning(
                "No matching news for this date/search. "
                "Try another keyword or click Reset."
            )
        else:
            st.info("No new updates right now.")
        return

    for pub, title, link, source in items:
        st.markdown(f"### {title}")
        st.write(f"🕒 {pub.strftime('%d %b %Y, %I:%M %p IST')}")
        st.markdown(
            f"<span style='background:#e5e7eb;padding:4px 8px;"
            f"border-radius:6px;font-size:12px;font-weight:600;'>📰 {source}</span>",
            unsafe_allow_html=True
        )
        st.markdown(f"[Open Article]({link})")
        st.divider()

# ------------------ TAB CONTENT ------------------
with tab_global:
    render_news(GLOBAL_FEEDS)

with tab_india:
    render_news(INDIA_FEEDS)

with tab_market:
    render_news(MARKET_FEEDS)
