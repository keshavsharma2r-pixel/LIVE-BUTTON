import streamlit as st
import feedparser
import time
from datetime import datetime, date
from zoneinfo import ZoneInfo
import socket, urllib.parse

# ================== TIMEZONE ==================
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")
socket.setdefaulttimeout(10)

# ================== PAGE ==================
st.set_page_config(layout="wide", page_title="News Intelligence Terminal")
st.title("📰 News Intelligence Terminal")

# ================== SESSION STATE ==================
if "live" not in st.session_state:
    st.session_state.live = False

if "search_only" not in st.session_state:
    st.session_state.search_only = False

if "seen" not in st.session_state:
    st.session_state.seen = set()

if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()

if "date_applied" not in st.session_state:
    st.session_state.date_applied = date.today()

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

if "manual_refresh" not in st.session_state:
    st.session_state.manual_refresh = False

if "last_refreshed" not in st.session_state:
    st.session_state.last_refreshed = datetime.now(IST)

# ================== CONTROLS ==================
col1, col2 = st.columns(2)

if col1.button("🚀 Start Live"):
    st.session_state.live = True
    st.session_state.search_only = False
    st.session_state.selected_date = date.today()
    st.session_state.date_applied = date.today()
    st.session_state.seen = set()
    st.session_state.last_refreshed = datetime.now(IST)

if col2.button("🛑 Stop"):
    st.session_state.live = False

refresh = st.slider("Refresh interval (seconds)", 20, 120, 30)

# ================== SEARCH ==================
search_col1, search_col2 = st.columns([3, 1])

with search_col1:
    search_input = st.text_input(
        "🔍 Search news (Google News)",
        placeholder="Reliance results, RBI policy, US inflation..."
    )

with search_col2:
    if st.button("🔍 Search News"):
        st.session_state.search_query = search_input.strip()
        st.session_state.search_only = bool(search_input.strip())
        st.session_state.live = False
        st.session_state.seen = set()
        st.session_state.last_refreshed = datetime.now(IST)

# ================== CALENDAR ==================
with st.form("date_form"):
    dcol1, dcol2 = st.columns([3, 1])

    with dcol1:
        temp_date = st.date_input(
            "📅 Select date (IST)",
            value=st.session_state.selected_date,
            max_value=date.today()
        )

    with dcol2:
        apply_date = st.form_submit_button("📅 Apply Date")

    if apply_date:
        st.session_state.selected_date = temp_date
        st.session_state.date_applied = temp_date
        st.session_state.live = False
        st.session_state.search_only = False
        st.session_state.seen = set()
        st.session_state.last_refreshed = datetime.now(IST)

# ================== CLOCK + REFRESH ==================
clock_col1, clock_col2 = st.columns([4, 1])

with clock_col1:
    now_ist = datetime.now(IST)
    st.markdown(
        f"""
        <div style="padding:8px 12px;
                    border-radius:8px;
                    background:#f1f5f9;
                    font-size:16px;
                    font-weight:600;
                    display:inline-block;">
            📅 {now_ist.strftime('%d %b %Y')}
            &nbsp; | &nbsp;
            ⏰ {now_ist.strftime('%I:%M:%S %p')} IST
        </div>
        """,
        unsafe_allow_html=True
    )

with clock_col2:
    st.button(
        "🔄 Refresh",
        disabled=st.session_state.live,
        help="Stop Live mode to refresh manually" if st.session_state.live else None,
        on_click=lambda: (
            st.session_state.seen.clear(),
            setattr(st.session_state, "manual_refresh", True),
            setattr(st.session_state, "last_refreshed", datetime.now(IST))
        )
    )

# ================== LAST REFRESHED ==================
st.caption(
    f"🔁 Last refreshed at: "
    f"{st.session_state.last_refreshed.strftime('%d %b %Y, %I:%M:%S %p IST')}"
)

# ================== MODE ==================
is_today = st.session_state.date_applied == date.today()

if st.session_state.search_only:
    st.success("🔍 SEARCH MODE (Google News)")
elif st.session_state.live and is_today:
    st.markdown(
        "<div style='color:white;background:red;padding:6px 12px;"
        "border-radius:6px;font-weight:bold;margin-top:8px;'>🔴 LIVE</div>",
        unsafe_allow_html=True
    )
elif st.session_state.live:
    st.warning("Live paused (historical date)")
else:
    st.info("Manual browsing mode")

# ================== HELPERS ==================
def safe_feed(url):
    try:
        return feedparser.parse(url)
    except:
        return None

def in_selected_date(pub_utc):
    return pub_utc.astimezone(IST).date() == st.session_state.date_applied

def google_news_search(query, context=""):
    q = urllib.parse.quote_plus(f"{query} {context}".strip())
    return f"https://news.google.com/rss/search?q={q}"

# ================== FEEDS ==================
GLOBAL_FEEDS = [
    "https://news.google.com/rss/search?q=world+news",
    "https://news.google.com/rss/search?q=business",
]

INDIA_FEEDS = [
    "https://news.google.com/rss/search?q=India",
]

NSE_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
]

BSE_FEEDS = [
    "https://www.livemint.com/rss/markets",
]

# ================== TABS ==================
tab_global, tab_india, tab_market = st.tabs(
    ["🌍 Global", "🇮🇳 India", "📈 Market"]
)

# ================== RENDER ==================
def render_news(feeds):
    items = []

    for url in feeds:
        feed = safe_feed(url)
        if not feed:
            continue

        for e in feed.entries:
            try:
                pub_utc = datetime(*e.published_parsed[:6], tzinfo=UTC)
            except:
                continue

            if not in_selected_date(pub_utc):
                continue

            if e.link in st.session_state.seen:
                continue

            items.append((pub_utc.astimezone(IST), e.title, e.link))

    items.sort(key=lambda x: x[0], reverse=True)

    if not items:
        st.warning("No news found.")

    for pub, title, link in items[:40]:
        st.markdown(f"### {title}")
        st.write(f"🕒 {pub.strftime('%d %b %Y, %I:%M %p IST')}")
        st.markdown(f"[Open Article]({link})")
        st.divider()

# ================== TAB CONTENT ==================
with tab_global:
    feeds = (
        [google_news_search(st.session_state.search_query, "world")]
        if st.session_state.search_only
        else GLOBAL_FEEDS
    )
    render_news(feeds)

with tab_india:
    feeds = (
        [google_news_search(st.session_state.search_query, "India")]
        if st.session_state.search_only
        else INDIA_FEEDS
    )
    render_news(feeds)

with tab_market:
    tab_nse, tab_bse = st.tabs(["📊 NSE", "🏦 BSE"])

    with tab_nse:
        feeds = (
            [google_news_search(st.session_state.search_query, "NSE stock market")]
            if st.session_state.search_only
            else NSE_FEEDS
        )
        render_news(feeds)

    with tab_bse:
        feeds = (
            [google_news_search(st.session_state.search_query, "BSE stock market")]
            if st.session_state.search_only
            else BSE_FEEDS
        )
        render_news(feeds)

# ================== MANUAL REFRESH (SAFE) ==================
if st.session_state.manual_refresh and not st.session_state.live:
    st.session_state.manual_refresh = False
    st.rerun()

# ================== AUTO REFRESH (LIVE) ==================
if st.session_state.live and is_today:
    time.sleep(refresh)
    st.session_state.last_refreshed = datetime.now(IST)
    st.rerun()
