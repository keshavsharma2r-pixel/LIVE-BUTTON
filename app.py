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

refresh = st.slider(
    "Auto refresh interval (seconds)",
    30, 300, 60,
    help="Controls how often news is refreshed automatically"
)

window = st.slider(
    "Show news from last (minutes)",
    60, 360, 180
)

# ------------------ LIVE BADGE ------------------
if st.session_state.live:
    st.markdown(
        "<div style='color:white;background:red;padding:6px 12px;"
        "border-radius:6px;font-weight:bold;'>🔴 LIVE (Cache-based)</div>",
        unsafe_allow_html=True
    )
else:
    st.info("Live mode OFF")

# ------------------ CACHED FEED (KEY FIX) ------------------
@st.cache_data(ttl=60)
def cached_feed(url):
    try:
        return feedparser.parse(url)
    except:
        return None

# ------------------ TIME FILTER ------------------
def is_recent(dt_utc):
    dt_ist = dt_utc.astimezone(IST)
    return dt_ist >= datetime.now(IST) - timedelta(minutes=window)

# ------------------ SOURCES ------------------
GLOBAL_FEEDS = [
    "https://news.google.com/rss/search?q=breaking+news",
    "https://news.google.com/rss/search?q=world+news",
    "https://news.google.com/rss/search?q=business",
    "https://news.google.com/rss/search?q=technology",
]

INDIA_GENERAL = [
    "https://news.google.com/rss/search?q=India",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
]

NSE_BASE = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml",
]

BSE_BASE = [
    "https://www.livemint.com/rss/markets",
]

NSE_COMPANIES = [
    "Reliance Industries", "Tata Motors", "HDFC Bank",
    "ICICI Bank", "Infosys", "TCS", "Adani Enterprises"
]

# ------------------ UI TABS ------------------
tab_global, tab_india, tab_market = st.tabs(
    ["🌍 Global", "🇮🇳 India General", "📈 India Market"]
)

# ------------------ DISPLAY FUNCTION ------------------
def render_news(feeds, company=None):
    items = []

    for url in feeds:
        feed = cached_feed(url)
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

            pub_ist = pub_utc.astimezone(IST)
            items.append((pub_ist, e.title, e.link))

    items.sort(key=lambda x: x[0], reverse=True)

    if not items:
        st.warning("No fresh news right now.")

    for pub_ist, title, link in items[:50]:
        st.session_state.seen.add(link)
        st.markdown(f"### {title}")
        st.write(f"🕒 {pub_ist.strftime('%d %b %Y, %I:%M %p IST')}")
        st.markdown(f"[Open]({link})")
        st.divider()

# ------------------ TAB: GLOBAL ------------------
with tab_global:
    st.subheader("🌍 Global Coverage")
    if st.session_state.live:
        render_news(GLOBAL_FEEDS)
    else:
        st.info("Start live to see global news")

# ------------------ TAB: INDIA ------------------
with tab_india:
    st.subheader("🇮🇳 India – General")
    if st.session_state.live:
        render_news(INDIA_GENERAL)
    else:
        st.info("Start live to see India news")

# ------------------ TAB: MARKET ------------------
with tab_market:
    tab_nse, tab_bse = st.tabs(["📊 NSE", "🏦 BSE"])

    with tab_nse:
        company = st.selectbox(
            "Filter NSE by company (optional)",
            ["All"] + NSE_COMPANIES
        )

        feeds = list(NSE_BASE)
        if company != "All":
            q = urllib.parse.quote_plus(f"{company} NSE stock")
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

# ------------------ STATUS ------------------
st.caption(
    f"Last checked: {datetime.now(IST).strftime('%d %b %Y, %I:%M:%S %p IST')} "
    f"| Auto refresh via cache (~{refresh}s)"
)
