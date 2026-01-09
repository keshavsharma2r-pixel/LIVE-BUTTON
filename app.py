import streamlit as st
import feedparser
from datetime import datetime
from zoneinfo import ZoneInfo
import socket
import urllib.parse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------ CONFIG ------------------
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")
socket.setdefaulttimeout(5)

st.set_page_config(
    layout="wide",
    page_title="NEWS PRO",
    page_icon="📰",
    initial_sidebar_state="collapsed"
)

# ------------------ SESSION STATE ------------------
if "seen" not in st.session_state:
    st.session_state.seen = set()

if "last_fetch" not in st.session_state:
    st.session_state.last_fetch = None

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

if "filter_date" not in st.session_state:
    st.session_state.filter_date = None

if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = {}

if "read_articles" not in st.session_state:
    st.session_state.read_articles = set()

if "force_live" not in st.session_state:
    st.session_state.force_live = False

if "settings" not in st.session_state:
    st.session_state.settings = {"view_mode": "list"}

# ------------------ CSS ------------------
st.markdown("""
<style>
.stApp { background:#0a0e1a; }
#MainMenu, footer, header {visibility:hidden;}

.main-header{
    background:linear-gradient(135deg,#1e3a8a,#312e81);
    padding:24px;border-radius:12px;margin-bottom:20px;
}

.header-title{color:white;font-size:32px;font-weight:800;}
.header-subtitle{color:rgba(255,255,255,0.7);font-size:14px;}

.article-card{
    background:#0f172a;border-left:3px solid #3b82f6;
    padding:20px;border-radius:8px;margin-bottom:14px;
}

.badge{
    font-size:11px;padding:4px 10px;border-radius:6px;
    margin-right:6px;display:inline-block;
}

.badge-live{background:#7f1d1d;color:#fecaca;}
.badge-time{background:#064e3b;color:#6ee7b7;}
.badge-category{background:#312e81;color:#c7d2fe;}
.badge-source{background:#1e3a8a;color:#bfdbfe;}

.compact-row{
    background:#1e293b;padding:10px;border-radius:6px;
    border-left:2px solid #3b82f6;margin-bottom:8px;
}
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
col_l, col_r = st.columns([6, 1])

with col_l:
    st.markdown("""
    <div class="main-header">
        <div class="header-title">📰 NEWS PRO</div>
        <div class="header-subtitle">Auto LIVE • Manual LIVE • Pro News Terminal</div>
    </div>
    """, unsafe_allow_html=True)

with col_r:
    if st.button("🔴 LIVE", use_container_width=True):
        st.session_state.force_live = True
        st.session_state.seen.clear()
        st.session_state.last_fetch = None
        st.rerun()

# ------------------ STATS ------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Articles", len(st.session_state.seen))
c2.metric("Read", len(st.session_state.read_articles))
c3.metric("Saved", len(st.session_state.bookmarks))
c4.metric(
    "Updated",
    st.session_state.last_fetch.strftime("%H:%M:%S") if st.session_state.last_fetch else "--"
)

# ------------------ FILTERS ------------------
f1, f2, f3 = st.columns([5, 2, 1])

with f1:
    search = st.text_input("Search", value=st.session_state.search_query, label_visibility="collapsed")

with f2:
    date_filter = st.date_input("Date", value=st.session_state.filter_date, label_visibility="collapsed")

with f3:
    if st.button("APPLY", use_container_width=True):
        st.session_state.search_query = search.strip()
        st.session_state.filter_date = date_filter
        st.session_state.seen.clear()
        st.rerun()

# ------------------ HELPERS ------------------
@st.cache_data(ttl=45)
def fetch_feed(url):
    return feedparser.parse(url)

def fetch_parallel(urls):
    feeds = []
    with ThreadPoolExecutor(max_workers=5) as exe:
        for f in as_completed([exe.submit(fetch_feed, u) for u in urls]):
            if f.result() and f.result().entries:
                feeds.append(f.result())
    return feeds

def freshness(ts):
    mins = int((datetime.now(IST) - ts).total_seconds() / 60)
    if mins <= 15:
        return "LIVE", "badge-live"
    return f"{mins//60}h", "badge-time"

# ------------------ FEEDS ------------------
GLOBAL_FEEDS = [
    "https://news.google.com/rss",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.reuters.com/rssFeed/worldNews"
]

INDIA_FEEDS = [
    "https://news.google.com/rss/search?q=India",
    "https://feeds.feedburner.com/ndtvnews-top-stories"
]

MARKET_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml"
]

# ------------------ RENDER ------------------
def render_news(feeds):
    REFRESH = 45
    now = datetime.now(IST)

    if not st.session_state.force_live and st.session_state.last_fetch:
        if (now - st.session_state.last_fetch).total_seconds() < REFRESH:
            return

    st.session_state.force_live = False
    st.session_state.last_fetch = now

    data = []
    for feed in fetch_parallel(feeds):
        for e in feed.entries[:15]:
            try:
                pub = datetime(*e.published_parsed[:6], tzinfo=UTC).astimezone(IST)
            except:
                continue

            if e.link in st.session_state.seen:
                continue

            if st.session_state.search_query:
                text = (e.title + getattr(e, "summary", "")).lower()
                if st.session_state.search_query.lower() not in text:
                    continue

            if st.session_state.filter_date and pub.date() != st.session_state.filter_date:
                continue

            st.session_state.seen.add(e.link)
            data.append((pub, e))

    data.sort(key=lambda x: x[0], reverse=True)

    if not data:
        st.info("No new articles")
        return

    for pub, e in data:
        tag, cls = freshness(pub)

        st.markdown(f"""
        <div class="article-card">
            <strong style="color:white">{e.title}</strong><br><br>
            <span class="badge badge-source">{urllib.parse.urlparse(e.link).netloc}</span>
            <span class="badge {cls}">{tag}</span>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("✓ Read", key=f"r_{e.link}"):
                st.session_state.read_articles.add(e.link)
                st.rerun()

        with c2:
            icon = "🔖" if e.link in st.session_state.bookmarks else "📑"
            if st.button(f"{icon} Save", key=f"b_{e.link}"):
                if e.link in st.session_state.bookmarks:
                    del st.session_state.bookmarks[e.link]
                else:
                    st.session_state.bookmarks[e.link] = {
                        "title": e.title,
                        "time": now.strftime("%Y-%m-%d %H:%M")
                    }
                st.rerun()

        with c3:
            st.link_button("Open", e.link)

# ------------------ TABS ------------------
tabs = st.tabs(["🌍 Global", "🇮🇳 India", "📈 Markets"])

with tabs[0]:
    render_news(GLOBAL_FEEDS)

with tabs[1]:
    render_news(INDIA_FEEDS)

with tabs[2]:
    render_news(MARKET_FEEDS)
