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

if "search_feeds" not in st.session_state:
    st.session_state.search_feeds = []

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
        "🔍 Search news (Google-powered)",
        placeholder="Reliance results, RBI policy, US inflation..."
    ).strip()

with search_col2:
    if st.button("🔍 Search News"):
        if search_query:
            q = urllib.parse.quote_plus(search_query)
            st.session_state.search_feeds = [
                f"https://news.google.com/rss/search?q={q}",
                f"https://news.google.com/rss/search?q={q}+India",
                f"https://news.google.com/rss/search?q={q}+stock+market",
            ]
            st.session_state.search_only = True
            st.session_state.live = False
            st.session_state.seen = set()

# ================== CALENDAR (APPLY) ==================
with st.form("date_form"):
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

# ================== CLOCK ==================
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

# ================== DATE BADGE ==================
st.markdown(
    f"""
    <div style="margin-top:6px;display:inline-block;
                background:#e0f2fe;color:#0369a1;
                padding:6px 10px;border-radius:999px;
                font-weight:600;font-size:14px;">
        📌 Showing news for: {st.session_state.date_applied.strftime('%d %b %Y')}
    </div>
    """,
    unsafe_allow_html=True
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

# ================== DEFAULT FEEDS ==================
GLOBAL_FEEDS = [
    "https://news.google.com/rss/search?q=breaking+news",
    "https://news.google.com/rss/search?q=world+news",
    "https://news.google.com/rss/search?q=business",
]

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

    for pub, title, link in items[:50]:
        st.markdown(f"### {title}")
        st.write(f"🕒 {pub.strftime('%d %b %Y, %I:%M %p IST')}")
        st.markdown(f"[Open Article]({link})")
        st.divider()

# ================== CONTENT ==================
if st.session_state.search_only:
    render_news(st.session_state.search_feeds)
else:
    render_news(GLOBAL_FEEDS)

# ================== AUTO REFRESH ==================
if st.session_state.live and is_today:
    time.sleep(refresh)
    st.rerun()
