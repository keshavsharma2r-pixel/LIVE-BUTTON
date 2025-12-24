import streamlit as st
import feedparser
from datetime import datetime, date
from zoneinfo import ZoneInfo
import urllib.parse

# ================= TIMEZONE =================
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")

st.set_page_config(page_title="News Intelligence Terminal", layout="wide")
st.title("📰 News Intelligence Terminal")

# ================= SESSION =================
if "seen" not in st.session_state:
    st.session_state.seen = set()
if "live" not in st.session_state:
    st.session_state.live = False
if "query" not in st.session_state:
    st.session_state.query = ""
if "date" not in st.session_state:
    st.session_state.date = date.today()
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now(IST)

# ================= CONTROLS =================
c1, c2, c3 = st.columns(3)

if c1.button("🚀 Start Live"):
    st.session_state.live = True
    st.session_state.seen.clear()
    st.session_state.last_refresh = datetime.now(IST)

if c2.button("🛑 Stop Live"):
    st.session_state.live = False

if c3.button("🔄 Refresh"):
    st.session_state.seen.clear()
    st.session_state.last_refresh = datetime.now(IST)

# ================= SEARCH =================
st.session_state.query = st.text_input(
    "🔍 Search news",
    st.session_state.query,
    placeholder="Reliance, RBI, US Fed..."
)

# ================= DATE =================
st.session_state.date = st.date_input(
    "📅 Select date",
    st.session_state.date,
    max_value=date.today()
)

# ================= CLOCK =================
now = datetime.now(IST)
st.markdown(
    f"""
    **📅 {now.strftime('%d %b %Y')} | ⏰ {now.strftime('%I:%M:%S %p')} IST**  
    🔁 Last refreshed: {st.session_state.last_refresh.strftime('%I:%M:%S %p')}
    """
)

# ================= FEED HELPERS =================
def gnews(q):
    q = urllib.parse.quote_plus(q)
    return f"https://news.google.com/rss/search?q={q}"

def render_news(url):
    feed = feedparser.parse(url)
    for e in feed.entries[:30]:
        try:
            pub = datetime(*e.published_parsed[:6], tzinfo=UTC).astimezone(IST)
        except:
            continue

        if pub.date() != st.session_state.date:
            continue
        if e.link in st.session_state.seen:
            continue

        st.session_state.seen.add(e.link)
        st.markdown(f"### {e.title}")
        st.write(pub.strftime("%d %b %Y, %I:%M %p IST"))
        st.markdown(f"[Open Article]({e.link})")
        st.divider()

# ================= TABS =================
t1, t2, t3 = st.tabs(["🌍 Global", "🇮🇳 India", "📈 Market"])

with t1:
    render_news(gnews(st.session_state.query or "world news"))

with t2:
    render_news(gnews(st.session_state.query or "India news"))

with t3:
    render_news(gnews(st.session_state.query or "stock market India"))

# ================= STATUS =================
if st.session_state.live:
    st.success("🔴 Live mode ON (manual refresh)")
else:
    st.info("Live mode OFF")
