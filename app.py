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

# ------------------ TOP RIGHT CONTROLS ------------------
top_left, top_right = st.columns([6, 2])

with top_right:
    if st.button("🔴 LIVE"):
        st.session_state.live = True
        st.session_state.seen.clear()
        st.session_state.last_fetch = None

    if st.button("⏹ STOP"):
        st.session_state.live = False

# ------------------ SEARCH + DATE ------------------
st.divider()

search_col, date_col, mode_col = st.columns([5, 2, 2])

with search_col:
    search_query = st.text_input(
        "🔍 Global Search (company, topic, keyword)",
        placeholder="Reliance, FED, AI, war, inflation..."
    )

with date_col:
    selected_date = st.date_input(
        "📅 Jump to date",
        value=date.today()
    )

with mode_col:
    search_only = st.checkbox("Search only (ignore live)")

# ------------------ STATUS ------------------
if st.session_state.live:
    st.markdown(
        "<div style='background:red;color:white;padding:6px 10px;"
        "border-radius:6px;font-weight:bold;width:max-content;'>🔴 LIVE</div>",
        unsafe_allow_html=True
    )
else:
    st.info("Live mode OFF")

# ------------------ FEED FETCH ------------------
def fetch_feed(url):
    try:
        return feedparser.parse(url)
    except:
        return None

# ------------------ SOURCE NAME ------------------
def get_source(entry):
    try:
        return urllib.parse.urlparse(entry.link).netloc.replace("www.", "").upper()
    except:
        return "UNKNOWN"

# ------------------ SOURCES (NO PRIORITY) ------------------
GOOGLE_FEEDS = [
    "https://news.google.com/rss",
    "https://news.google.com/rss/search?q=business",
    "https://news.google.com/rss/search?q=markets",
    "https://news.google.com/rss/search?q=world",
    "https://news.google.com/rss/search?q=India",
]

GLOBAL_FEEDS = [
    "https://www.reuters.com/rssFeed/worldNews",
    "https://www.reuters.com/rssFeed/businessNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
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

# ------------------ RENDER FUNCTION ------------------
def render_news(feeds):
    FETCH_INTERVAL = 60
    now = datetime.now(IST)

    if st.session_state.live and not search_only:
        if st.session_state.last_fetch:
            if (now - st.session_state.last_fetch).total_seconds() < FETCH_INTERVAL:
                return
        st.session_state.last_fetch = now

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

            pub_ist = pub_utc.astimezone(IST)

            # Date filter (calendar jump)
            if pub_ist.date() != selected_date:
                continue

            # Search filter
            if search_query:
                text = f"{e.title} {getattr(e,'summary','')}".lower()
                if search_query.lower() not in text:
                    continue

            if e.link in st.session_state.seen:
                continue

            st.session_state.seen.add(e.link)

            collected.append((
                pub_ist,
                e.title,
                e.link,
                get_source(e)
            ))

    collected.sort(key=lambda x: x[0], reverse=True)

    if not collected:
        st.warning("No news found for selected filters.")
        return

    for pub, title, link, source in collected:
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
    render_news(GOOGLE_FEEDS + GLOBAL_FEEDS)

with tab_india:
    render_news(GOOGLE_FEEDS)

with tab_market:
    render_news(MARKET_FEEDS)
