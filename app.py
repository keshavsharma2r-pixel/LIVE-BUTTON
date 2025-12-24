import streamlit as st
import feedparser
import time
from datetime import datetime, date
from zoneinfo import ZoneInfo
import socket, urllib.parse

# ================== OPTIONAL AUTOCLOCK ==================
try:
    from streamlit_autorefresh import st_autorefresh
    AUTO_CLOCK = True
except Exception:
    AUTO_CLOCK = False

# ================== TIMEZONE ==================
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")
socket.setdefaulttimeout(10)

# ================== PAGE ==================
st.set_page_config(layout="wide", page_title="News Intelligence Terminal")
st.title("📰 News Intelligence Terminal")

# ================== SESSION STATE ==================
defaults = {
    "live": False,
    "search_only": False,
    "seen": set(),
    "selected_date": date.today(),
    "date_applied": date.today(),
    "search_query": "",
    "manual_refresh": False,
    "last_refreshed": datetime.now(IST),
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================== CONTROLS ==================
c1, c2 = st.columns(2)

if c1.button("🚀 Start Live"):
    st.session_state.live = True
    st.session_state.search_only = False
    st.session_state.selected_date = date.today()
    st.session_state.date_applied = date.today()
    st.session_state.seen.clear()
    st.session_state.last_refreshed = datetime.now(IST)

if c2.button("🛑 Stop"):
    st.session_state.live = False

refresh = st.slider("Refresh interval (seconds)", 20, 120, 30)

# ================== SEARCH ==================
s1, s2 = st.columns([3, 1])

with s1:
    search_input = st.text_input(
        "🔍 Search news (Google News)",
        placeholder="Reliance results, RBI policy, US inflation..."
    )

with s2:
    if st.button("🔍 Search News"):
        st.session_state.search_query = search_input.strip()
        st.session_state.search_only = bool(search_input.strip())
        st.session_state.live = False
        st.session_state.seen.clear()
        st.session_state.last_refreshed = datetime.now(IST)

# ================== CALENDAR ==================
with st.form("date_form"):
    d1, d2 = st.columns([3, 1])
    with d1:
        temp_date = st.date_input(
            "📅 Select date (IST)",
            value=st.session_state.selected_date,
            max_value=date.today()
        )
    with d2:
        apply_date = st.form_submit_button("📅 Apply Date")

    if apply_date:
        st.session_state.selected_date = temp_date
        st.session_state.date_applied = temp_date
        st.session_state.live = False
        st.session_state.search_only = False
        st.session_state.seen.clear()
        st.session_state.last_refreshed = datetime.now(IST)

# ================== INDEPENDENT CLOCK (SAFE) ==================
if AUTO_CLOCK:
    st_autorefresh(interval=1000, key="clock_only")

# ================== CLOCK + REFRESH ==================
t1, t2 = st.columns([4, 1])

with t1:
    now_ist = datetime.now(IST)
    st.markdown(
        f"""
        <div style="padding:8px 12px;border-radius:8px;
        background:#f1f5f9;font-size:16px;font-weight:600;">
        📅 {now_ist.strftime('%d %b %Y')}
        &nbsp; | &nbsp;
        ⏰ {now_ist.strftime('%I:%M:%S %p')} IST
        </div>
        """,
        unsafe_allow_html=True
    )

with t2:
    st.button(
        "🔄 Refresh",
        disabled=st.session_state.live,
        help="Stop Live to refresh manually",
        on_click=lambda: (
            st.session_state.seen.clear(),
            setattr(st.session_state, "manual_refresh", True),
            setattr(st.session_state, "last_refreshed", datetime.now(IST))
        )
    )

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
        "<div style='background:red;color:white;padding:6px 12px;"
        "border-radius:6px;font-weight:bold;'>🔴 LIVE</div>",
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
    except Exception:
        return None

def in_selected_date(pub):
    return pub.astimezone(IST).date() == st.session_state.date_applied

def gnews(q, ctx=""):
    q = urllib.parse.quote_plus(f"{q} {ctx}".strip())
    return f"https://news.google.com/rss/search?q={q}"

# ================== FEEDS ==================
GLOBAL = ["https://news.google.com/rss/search?q=world+news"]
INDIA = ["https://news.google.com/rss/search?q=India"]
NSE = ["https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"]
BSE = ["https://www.livemint.com/rss/markets"]

# ================== TABS ==================
tg, ti, tm = st.tabs(["🌍 Global", "🇮🇳 India", "📈 Market"])

def render(feeds):
    items = []
    for u in feeds:
        f = safe_feed(u)
        if not f:
            continue
        for e in f.entries:
            try:
                pub = datetime(*e.published_parsed[:6], tzinfo=UTC)
            except Exception:
                continue
            if not in_selected_date(pub):
                continue
            if e.link in st.session_state.seen:
                continue
            items.append((pub.astimezone(IST), e.title, e.link))
    items.sort(reverse=True)
    for p, t, l in items[:40]:
        st.markdown(f"### {t}")
        st.write(p.strftime("%d %b %Y, %I:%M %p IST"))
        st.markdown(f"[Open]({l})")
        st.divider()

with tg:
    render([gnews(st.session_state.search_query, "world")] if st.session_state.search_only else GLOBAL)

with ti:
    render([gnews(st.session_state.search_query, "India")] if st.session_state.search_only else INDIA)

with tm:
    tn, tb = st.tabs(["📊 NSE", "🏦 BSE"])
    with tn:
        render([gnews(st.session_state.search_query, "NSE")] if st.session_state.search_only else NSE)
    with tb:
        render([gnews(st.session_state.search_query, "BSE")] if st.session_state.search_only else BSE)

# ================== MANUAL REFRESH ==================
if st.session_state.manual_refresh and not st.session_state.live:
    st.session_state.manual_refresh = False
    st.rerun()

# ================== LIVE AUTO REFRESH ==================
if st.session_state.live and is_today:
    time.sleep(refresh)
    st.session_state.last_refreshed = datetime.now(IST)
    st.rerun()
