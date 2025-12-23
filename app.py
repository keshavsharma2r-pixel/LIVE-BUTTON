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

# ================== CONTROLS ==================
col1, col2 = st.columns(2)

if col1.button("🚀 Start Live"):
    st.session_state.live = True
    st.session_state.search_only = False
    st.session_state.selected_date = date.today()
    st.session_state.date_applied = date.today()
    st.session_state.seen = set()

if col2.button("🛑 Stop"):
    st.session_state.live = False

refresh = st.slider("Refresh interval (seconds)", 20, 120, 30)

# ================== SEARCH ==================
search_col1, search_col2 = st.columns([3, 1])

with search_col1:
    search_query = st.text_input(
        "🔍 Search news (company, topic, keyword)",
        placeholder="Reliance, IPO, inflation..."
    ).strip().lower()

with search_col2:
    if st.button("🔍 Search News"):
        st.session_state.search_only = True
        st.session_state.live = False
        st.session_state.seen = set()

# ================== CALENDAR FORM (ENTER WORKS) ==================
with st.form("date_form", clear_on_submit=False):
    date_col1, date_col2 = st.columns([3, 1])

    with date_col1:
        temp_date = st.date_input(
            "📅 Select date (IST)",
            value=st.session_state.selected_date,
            max_value=date.today()
        )

    with date_col2:
        apply_date = st.form_submit_button("📅 Apply Date")

    if apply_date:
        st.session_state.selected_date = temp_date
        st.session_state.date_applied = temp_date
        st.session_state.live = False
        st.session_state.search_only = False
        st.session_state.seen = set()

# ================== LIVE DATE & TIME ==================
now_ist = datetime.now(IST)
st.markdown(
    f"""
    <div style="margin-top:10px;padding:8px 12px;
                border-radius:8px;background:#f1f5f9;
                font-size:16px;font-weight:600;display:inline-block;">
        📅 {now_ist.strftime('%d %b %Y')}
        &nbsp; | &nbsp;
        ⏰ {now_ist.strftime('%I:%M:%S %p')} IST
    </div>
    """,
    unsafe_allow_html=True
)

# ================== APPLIED DATE BADGE (41) ==================
st.markdown(
    f"""
    <div style="margin-top:6px;
                display:inline-block;
                background:#e0f2fe;
                color:#0369a1;
                padding:6px 10px;
                border-radius:999px;
                font-weight:600;
                font-size:14px;">
        📌 Showing news for: {st.session_state.date_applied.strftime('%d %b %Y')}
    </div>
    """,
    unsafe_allow_html=True
)

# ================== MODE INDICATOR ==================
is_today = st.session_state.date_applied == date.today()

if st.session_state.search_only:
    st.success("🔍 SEARCH MODE (Live disabled)")
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

def matches_search(text):
    if not search_query:
        return True
    return search_query in text

# ================== SOURCES ==================
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

# ================== TABS ==================
tab_global, tab_india, tab_market = st.tabs(
    ["🌍 Global", "🇮🇳 India General", "📈 India Market"]
)

# ================== RENDER ==================
def render_news(feeds, company=None):
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

            text = f"{e.title} {getattr(e,'summary','')}".lower()

            if company and company.lower() not in text:
                continue

            if not matches_search(text):
                continue

            if e.link in st.session_state.seen:
                continue

            items.append((pub_utc.astimezone(IST), e.title, e.link))

    items.sort(key=lambda x: x[0], reverse=True)

    if not items:
        st.warning("No news found.")

    for pub, title, link in items[:50]:
        st.markdown(f"### {title}")
        st.write(f"🕒 {pub.strftime('%d %b %Y, %I:%M %p IST')}")
        st.markdown(f"[Open Article]({link})")
        st.divider()

# ================== GLOBAL ==================
with tab_global:
    render_news(GLOBAL_FEEDS)

# ================== INDIA ==================
with tab_india:
    render_news(INDIA_GENERAL)

# ================== MARKET ==================
with tab_market:
    tab_nse, tab_bse = st.tabs(["📊 NSE", "🏦 BSE"])

    with tab_nse:
        company = st.selectbox("Filter NSE by company", ["All"] + NSE_COMPANIES)
        feeds = list(NSE_BASE)
        if company != "All":
            q = urllib.parse.quote_plus(f"{company} NSE stock")
            feeds.append(f"https://news.google.com/rss/search?q={q}")
        render_news(feeds, None if company == "All" else company)

    with tab_bse:
        render_news(BSE_BASE)

# ================== AUTO REFRESH ==================
if st.session_state.live and is_today:
    st.caption(
        f"Last updated: {datetime.now(IST).strftime('%d %b %Y, %I:%M:%S %p IST')}"
    )
    time.sleep(refresh)
    st.rerun()
