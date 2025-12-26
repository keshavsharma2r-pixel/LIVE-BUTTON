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

# ------------------ CONTROLS ------------------
col1, col2 = st.columns(2)

if col1.button("🚀 Start Live"):
    st.session_state.live = True
    st.session_state.seen.clear()

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
    dt_ist = dt_utc.astimezone(IST)
    return dt_ist >= datetime.now(IST) - timedelta(minutes=window)

def get_source(entry):
    if hasattr(entry, "source") and hasattr(entry.source, "title"):
        return entry.source.title
    try:
        domain = urllib.parse.urlparse(entry.link).netloc
        return domain.replace("www.", "").upper()
    except:
        return "UNKNOWN"

# ------------------ SOURCES ------------------

# 🌍 GOOGLE NEWS – GLOBAL AGGREGATOR
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

# 🏛️ TIER-1 GLOBAL PUBLISHERS
GLOBAL_TIER1 = [
    "https://www.reuters.com/rssFeed/worldNews",
    "https://www.reuters.com/rssFeed/businessNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
]

# 🌎 REGIONAL / CONTINENTAL
REGIONAL_GLOBAL = [
    "https://news.google.com/rss/search?q=asia+markets",
    "https://news.google.com/rss/search?q=europe+markets",
    "https://news.google.com/rss/search?q=middle+east+news",
    "https://news.google.com/rss/search?q=africa+economy",
    "https://news.google.com/rss/search?q=latin+america+markets",
]

# 🇮🇳 INDIA – GENERAL
INDIA_GENERAL = [
    "https://news.google.com/rss/search?q=India+breaking+news",
    "https://news.google.com/rss/search?q=India+economy",
    "https://news.google.com/rss/search?q=India+markets",
    "https://news.google.com/rss/search?q=RBI+policy",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
]

# 📈 INDIA MARKETS
NSE_BASE = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://www.livemint.com/rss/markets",
]

BSE_BASE = [
    "https://www.livemint.com/rss/markets",
]

NSE_COMPANIES = [
    "Reliance Industries", "Tata Motors", "HDFC Bank",
    "ICICI Bank", "Infosys", "TCS", "Adani Enterprises"
]

GLOBAL_FEEDS = GOOGLE_GLOBAL + GLOBAL_TIER1 + REGIONAL_GLOBAL

# ------------------ UI TABS ------------------
tab_global, tab_india, tab_market = st.tabs(
    ["🌍 Global", "🇮🇳 India General", "📈 India Market"]
)

# ------------------ RENDER NEWS ------------------
def render_news(feeds, company=None):
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

            text = f"{e.title} {getattr(e,'summary','')}".lower()
            if company and company.lower() not in text:
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

    if not items:
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
    tab_nse, tab_bse = st.tabs(["📊 NSE", "🏦 BSE"])

    with tab_nse:
        company = st.selectbox("Filter NSE company", ["All"] + NSE_COMPANIES)
        feeds = list(NSE_BASE)
        if company != "All":
            q = urllib.parse.quote_plus(company + " stock")
            feeds.append(f"https://news.google.com/rss/search?q={q}")

        if st.session_state.live:
            render_news(feeds, None if company == "All" else company)
        else:
            st.info("Start live to see NSE news")

    with tab_bse:
        if st.session_state.live:
            render_news(BSE_BASE)
        else:
            st.info("Start live to see BSE news")
