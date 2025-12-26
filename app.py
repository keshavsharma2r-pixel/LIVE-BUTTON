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
if "last_update" not in st.session_state:
    st.session_state.last_update = None

# ------------------ CONTROLS ------------------
col1, col2 = st.columns(2)

if col1.button("🚀 Start Live"):
    st.session_state.live = True
    st.session_state.seen.clear()
    st.session_state.last_update = datetime.now(IST)

if col2.button("🛑 Stop"):
    st.session_state.live = False

window = st.slider(
    "Show news from last (minutes)",
    60, 360, 180
)

# ------------------ LIVE BADGE ------------------
if st.session_state.live:
    st.markdown(
        "<div style='color:white;background:red;padding:6px 12px;"
        "border-radius:6px;font-weight:bold;'>🔴 LIVE</div>",
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

# ------------------ HELPERS ------------------
def is_recent(dt_utc):
    return dt_utc.astimezone(IST) >= datetime.now(IST) - timedelta(minutes=window)

def get_source(entry):
    if hasattr(entry, "source") and hasattr(entry.source, "title"):
        return entry.source.title
    try:
        domain = urllib.parse.urlparse(entry.link).netloc
        return domain.replace("www.", "").upper()
    except:
        return "UNKNOWN"

# ------------------ SOURCES ------------------

GOOGLE_GLOBAL = [
    "https://news.google.com/rss/search?q=breaking+news",
    "https://news.google.com/rss/search?q=world+news",
    "https://news.google.com/rss/search?q=global+markets",
    "https://news.google.com/rss/search?q=business+news",
    "https://news.google.com/rss/search?q=technology+news",
    "https://news.google.com/rss/search?q=geopolitics",
    "https://news.google.com/rss/search?q=war+conflict",
    "https://news.google.com/rss/search?q=inflation+interest+rates",
    "https://news.google.com/rss/search?q=central+bank+policy",
]

GLOBAL_TIER1 = [
    "https://www.reuters.com/rssFeed/worldNews",
    "https://www.reuters.com/rssFeed/businessNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
]

REGIONAL_GLOBAL = [
    "https://news.google.com/rss/search?q=asia+markets",
    "https://news.google.com/rss/search?q=europe+markets",
    "https://news.google.com/rss/search?q=middle+east+news",
    "https://news.google.com/rss/search?q=africa+economy",
    "https://news.google.com/rss/search?q=latin+america+markets",
]

INDIA_GENERAL = [
    "https://news.google.com/rss/search?q=India+breaking+news",
    "https://news.google.com/rss/search?q=India+economy",
    "https://news.google.com/rss/search?q=India+markets",
    "https://news.google.com/rss/search?q=RBI+policy",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
]

MARKET_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://www.livemint.com/rss/markets",
    "https://news.google.com/rss/search?q=stock+market+news",
    "https://news.google.com/rss/search?q=global+markets",
    "https://news.google.com/rss/search?q=earnings+results",
    "https://news.google.com/rss/search?q=mergers+acquisitions",
    "https://www.reuters.com/rssFeed/businessNews",
]

GLOBAL_FEEDS = GOOGLE_GLOBAL + GLOBAL_TIER1 + REGIONAL_GLOBAL

# ------------------ UI TABS ------------------
tab_global, tab_india, tab_market = st.tabs(
    ["🌍 Global", "🇮🇳 India General", "📈 Market"]
)

# ------------------ RENDER NEWS ------------------
def render_news(feeds):
    items = []

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

            items.append((
                pub_utc.astimezone(IST),
                e.title,
                e.link,
                get_source(e)
            ))

    items.sort(key=lambda x: x[0], reverse=True)

    if items:
        st.session_state.last_update = datetime.now(IST)
    else:
        st.warning("No fresh news right now.")

    for pub_ist, title, link, source in items[:50]:
        st.session_state.seen.add(link)

        st.markdown(f"### {title}")
        st.write(f"🕒 {pub_ist.strftime('%d %b %Y, %I:%M %p IST')}")
        st.markdown(
            f"<span style='background:#e5e7eb;padding:4px 8px;"
            f"border-radius:6px;font-size:12px;font-weight:600;'>"
            f"📰 {source}</span>",
            unsafe_allow_html=True
        )
        st.markdown(f"[Open Article]({link})")
        st.divider()

# ------------------ GLOBAL ------------------
with tab_global:
    if st.session_state.live:
        render_news(GLOBAL_FEEDS)
    else:
        st.info("Start live to see global news")

# ------------------ INDIA ------------------
with tab_india:
    if st.session_state.live:
        render_news(INDIA_GENERAL)
    else:
        st.info("Start live to see India news")

# ------------------ MARKET ------------------
with tab_market:
    if st.session_state.live:
        render_news(MARKET_FEEDS)
    else:
        st.info("Start live to see market news")

# ------------------ LAST UPDATE DISPLAY ------------------
if st.session_state.last_update:
    st.markdown(
        f"""
        <div style="
            background:#f8fafc;
            padding:10px 14px;
            border-radius:8px;
            font-size:14px;
            font-weight:600;
            margin-top:14px;
        ">
            ⏱ <b>Last Update:</b>
            {st.session_state.last_update.strftime('%d %b %Y, %I:%M %p IST')}
        </div>
        """,
        unsafe_allow_html=True
    )
