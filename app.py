import streamlit as st
import feedparser
from datetime import datetime, date
from zoneinfo import ZoneInfo
import urllib.parse

# ================== TIMEZONE ==================
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")

st.set_page_config(layout="wide", page_title="News Intelligence Terminal")
st.title("📰 News Intelligence Terminal")

# ================== SESSION ==================
if "live" not in st.session_state:
    st.session_state.live = False
if "seen" not in st.session_state:
    st.session_state.seen = set()
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "date_applied" not in st.session_state:
    st.session_state.date_applied = date.today()
if "last_refreshed" not in st.session_state:
    st.session_state.last_refreshed = datetime.now(IST)

# ================== CONTROLS ==================
c1, c2, c3 = st.columns(3)

if c1.button("🚀 Start Live"):
    st.session_state.live = True
    st.session_state.seen.clear()
    st.session_state.last_refreshed = datetime.now(IST)

if c2.button("🛑 Stop Live"):
    st.session_state.live = False

if c3.button("🔄 Refresh Now"):
    st.session_state.seen.clear()
    st.session_state.last_refreshed = datetime.now(IST)

# ================== SEARCH ==================
st.session_state.search_query = st.text_input(
    "🔍 Search news",
    value=st.session_state.search_query
)

# ================== DATE ==================
st.session_state.date_applied = st.date_input(
    "📅 Select date",
    value=st.session_state.date_applied,
    max_value=date.today()
)

# ================== CLOCK ==================
now = datetime.now(IST)
st.markdown(
    f"""
    **📅 {now.strftime('%d %b %Y')} | ⏰ {now.strftime('%I:%M:%S %p')} IST**  
    🔁 Last refreshed: {st.session_state.last_refreshed.strftime('%I:%M:%S %p')}
    """
)

# ================== FEED HELPERS ==================
def google_news(q):
    q = urllib.parse.quote_plus(q)
    return f"https://news.google.com/rss/search?q={q}"

def render_news(url):
    feed = feedparser.parse(url)
    for e in feed.entries[:30]:
        try:
            pub = datetime(*e.published_parsed[:6], tzinfo=UTC).astimezone(IST)
        except:
            continue

        if pub.date() != st.session_state.date_applied:
            continue
        if e.link in st.session_state.seen:
            continue

        st.session_state.seen.add(e.link)
        st.markdown(f"### {e.title}")
        st.write(pub.strftime("%d %b %Y, %I:%M %p IST"))
        st.markdown(f"[Open Article]({e.link})")
        st.divider()

# ================== TABS ==================
tab1, tab2, tab3 = st.tabs(["🌍 Global", "🇮🇳 India", "📈 Market"])

with tab1:
    render_news(google_news(st.session_state.search_query or "world news"))

with tab2:
    render_news(google_news(st.session_state.search_query or "India news"))

with tab3:
    render_news(google_news(st.session_state.search_query or "stock market India"))

# ================== LIVE MODE MESSAGE ==================
if st.session_state.live:
    st.success("🔴 Live mode ON (click Refresh to fetch latest)")
else:
    st.info("Live mode OFF")
