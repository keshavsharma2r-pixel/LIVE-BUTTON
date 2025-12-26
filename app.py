import streamlit as st
import feedparser
from datetime import datetime, date
from zoneinfo import ZoneInfo
import socket
import urllib.parse
import time

# ------------------ TIMEZONE ------------------
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")
socket.setdefaulttimeout(10)

# ------------------ PAGE CONFIG ------------------
st.set_page_config(layout="wide", page_title="NEWS", page_icon="📰")
st.title("📰 NEWS")

# ------------------ SESSION STATE ------------------
if "live" not in st.session_state:
    st.session_state.live = False
if "seen" not in st.session_state:
    st.session_state.seen = set()
if "last_fetch" not in st.session_state:
    st.session_state.last_fetch = None

# FILTER STATE
if "apply_filters" not in st.session_state:
    st.session_state.apply_filters = False
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "filter_date" not in st.session_state:
    st.session_state.filter_date = None

# ------------------ TOP CONTROLS ------------------
col1, col2, col3 = st.columns([6, 1, 1])

with col2:
    if st.button("🔴 LIVE", use_container_width=True):
        st.session_state.live = True
        st.session_state.seen.clear()
        st.session_state.last_fetch = None
        st.rerun()

with col3:
    if st.button("⏹ STOP", use_container_width=True):
        st.session_state.live = False
        st.rerun()

# ------------------ FILTER CONTROLS ------------------
st.divider()

f1, f2, f3, f4 = st.columns([5, 2, 1.5, 1.5])

with f1:
    search_input = st.text_input(
        "🔍 Search",
        placeholder="Company, keyword, topic…",
        value=st.session_state.search_query,
        key="search_input"
    )

with f2:
    date_input = st.date_input(
        "📅 Date",
        value=st.session_state.filter_date,
        key="date_input"
    )

with f3:
    if st.button("🔍 Apply", use_container_width=True):
        st.session_state.search_query = search_input.strip()
        st.session_state.filter_date = date_input
        st.session_state.apply_filters = bool(search_input.strip() or date_input)
        st.session_state.seen.clear()
        st.rerun()

with f4:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.apply_filters = False
        st.session_state.search_query = ""
        st.session_state.filter_date = None
        st.session_state.seen.clear()
        st.rerun()

# ------------------ STATUS BAR ------------------
status_col1, status_col2 = st.columns([1, 3])

with status_col1:
    if st.session_state.live:
        st.markdown(
            "<div style='background:#ef4444;color:white;padding:8px 12px;"
            "border-radius:8px;font-weight:bold;text-align:center;'>"
            "🔴 LIVE MODE</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='background:#64748b;color:white;padding:8px 12px;"
            "border-radius:8px;font-weight:bold;text-align:center;'>"
            "⏹ STOPPED</div>",
            unsafe_allow_html=True
        )

with status_col2:
    if st.session_state.last_fetch:
        last_update = st.session_state.last_fetch.strftime("%I:%M:%S %p")
        st.info(f"🕐 Last updated: {last_update}")

st.divider()

# ------------------ FEED FETCH ------------------
@st.cache_data(ttl=60)
def fetch_feed(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        return feedparser.parse(url, request_headers=headers)
    except Exception as e:
        st.error(f"Error fetching {url}: {str(e)}")
        return None

def get_source(entry):
    try:
        domain = urllib.parse.urlparse(entry.link).netloc.replace("www.", "")
        return domain.split('.')[0].upper()
    except:
        return "UNKNOWN"

# ------------------ FRESHNESS TAG ------------------
def freshness_label(pub_time):
    delta = datetime.now(IST) - pub_time
    minutes = int(delta.total_seconds() / 60)

    if minutes < 0:
        return "🔵 FUTURE", "Just now"
    elif minutes <= 15:
        return "🟢 LIVE", f"{minutes} min ago"
    elif minutes <= 120:
        hours = minutes // 60
        mins = minutes % 60
        return "🟡 RECENT", f"{hours}h {mins}m ago"
    elif minutes <= 1440:  # 24 hours
        return "⚪ TODAY", f"{minutes // 60}h ago"
    else:
        days = minutes // 1440
        return "⚫ OLDER", f"{days}d ago"

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
def render_news(feeds, tab_name):
    FETCH_INTERVAL = 60
    now = datetime.now(IST)

    # Handle live mode refresh logic
    if st.session_state.live:
        if st.session_state.last_fetch:
            elapsed = (now - st.session_state.last_fetch).total_seconds()
            if elapsed < FETCH_INTERVAL:
                time.sleep(2)
                st.rerun()
                return
        st.session_state.last_fetch = now

    # Show loading indicator
    with st.spinner(f"Fetching {tab_name} news..."):
        collected = []

        for url in feeds:
            feed = fetch_feed(url)
            if not feed or not feed.entries:
                continue

            for e in feed.entries:
                try:
                    # Parse publication time
                    if hasattr(e, 'published_parsed') and e.published_parsed:
                        pub_utc = datetime(*e.published_parsed[:6], tzinfo=UTC)
                    elif hasattr(e, 'updated_parsed') and e.updated_parsed:
                        pub_utc = datetime(*e.updated_parsed[:6], tzinfo=UTC)
                    else:
                        continue
                    
                    pub_ist = pub_utc.astimezone(IST)
                except Exception:
                    continue

                # Apply filters
                if st.session_state.apply_filters:
                    if st.session_state.filter_date:
                        if pub_ist.date() != st.session_state.filter_date:
                            continue

                    if st.session_state.search_query:
                        text = f"{e.title} {getattr(e, 'summary', '')}".lower()
                        if st.session_state.search_query.lower() not in text:
                            continue

                # Skip duplicates
                if e.link in st.session_state.seen:
                    continue

                st.session_state.seen.add(e.link)
                collected.append((pub_ist, e.title, e.link, get_source(e)))

    # Sort by time (newest first)
    collected.sort(key=lambda x: x[0], reverse=True)

    # Display article count
    if collected:
        st.success(f"📊 Found {len(collected)} articles")
    
    # Handle empty state
    if not collected:
        if st.session_state.apply_filters:
            st.warning("🔍 No articles match your filters. Try adjusting search terms or date.")
        else:
            st.info("📭 No new articles at the moment. Check back soon!")
        return

    # Render articles
    for pub, title, link, source in collected:
        tag, age = freshness_label(pub)

        with st.container():
            st.markdown(f"### {title}")
            
            info_col1, info_col2 = st.columns([2, 3])
            with info_col1:
                st.markdown(
                    f"<span style='background:#e5e7eb;padding:4px 10px;"
                    f"border-radius:6px;font-size:13px;font-weight:600;'>"
                    f"📰 {source}</span>",
                    unsafe_allow_html=True
                )
            with info_col2:
                st.write(f"{tag} • {age}")
            
            st.markdown(f"🔗 [Read Full Article]({link})")
            st.divider()

    # Auto-refresh in live mode
    if st.session_state.live:
        time.sleep(FETCH_INTERVAL)
        st.rerun()

# ------------------ TAB CONTENT ------------------
with tab_global:
    render_news(GLOBAL_FEEDS, "Global")

with tab_india:
    render_news(INDIA_FEEDS, "India")

with tab_market:
    render_news(MARKET_FEEDS, "Market")
