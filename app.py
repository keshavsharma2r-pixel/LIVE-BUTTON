import streamlit as st
import time
import feedparser
from datetime import datetime, timezone, timedelta
import urllib.parse

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(layout="wide", page_title="🇮🇳 LIVE INDIA NEWS TERMINAL")

st.title("🇮🇳 LIVE INDIA NEWS (GENERAL • MARKET • NSE • BSE)")

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "live" not in st.session_state:
    st.session_state.live = False

if "seen_links" not in st.session_state:
    st.session_state.seen_links = set()

if "last_check" not in st.session_state:
    st.session_state.last_check = datetime.now(timezone.utc) - timedelta(minutes=30)

# -------------------------------------------------
# TOP CONTROLS
# -------------------------------------------------
news_type = st.radio(
    "Select News Category",
    ["🇮🇳 India – General", "📈 India – Market"],
    horizontal=True
)

col1, col2 = st.columns(2)

if col1.button("🚀 Start Live Updates"):
    st.session_state.live = True

if col2.button("🛑 Stop Live"):
    st.session_state.live = False

refresh_interval = st.slider("Refresh Interval (seconds)", 5, 30, 10)
latest_minutes = st.slider("Consider news from last (minutes)", 5, 60, 20)

# -------------------------------------------------
# FLASHING LIVE BADGE
# -------------------------------------------------
if st.session_state.live:
    badge_text = "🔴 LIVE INDIA" if "General" in news_type else "🔴 LIVE MARKET"
    st.markdown(
        f"""
        <style>
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
            100% {{ opacity: 1; }}
        }}
        .live-badge {{
            color: white;
            background: red;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: bold;
            display: inline-block;
            animation: pulse 1s infinite;
        }}
        </style>
        <div class="live-badge">{badge_text}</div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown("⚪ LIVE OFF")

placeholder = st.empty()

# -------------------------------------------------
# SOURCES
# -------------------------------------------------
INDIA_GENERAL_SOURCES = [
    "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
    "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
]

NSE_BASE_SOURCES = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml",
]

BSE_SOURCES = [
    "https://www.livemint.com/rss/markets",
    "https://news.google.com/rss/search?q=BSE+Sensex+India+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
]

# -------------------------------------------------
# NSE COMPANY LIST (EXTEND LATER)
# -------------------------------------------------
NSE_COMPANIES = [
    "Reliance Industries",
    "Tata Motors",
    "HDFC Bank",
    "ICICI Bank",
    "Infosys",
    "TCS",
    "Wipro",
    "HUL",
    "ITC",
    "Adani Enterprises"
]

# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------
def time_ago(published_time):
    now = datetime.now(timezone.utc)
    diff = now - published_time
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"

def process_sources(sources, company=None):
    fresh = []

    for src in sources:
        feed = feedparser.parse(src)

        for item in feed.entries:
            text = f"{item.title} {getattr(item, 'summary', '')}".lower()

            if company and company.lower() not in text:
                continue

            try:
                pub_time = datetime(*item.published_parsed[:6], tzinfo=timezone.utc)
            except:
                continue

            if pub_time < datetime.now(timezone.utc) - timedelta(minutes=latest_minutes):
                continue

            if pub_time <= st.session_state.last_check:
                continue

            if item.link in st.session_state.seen_links:
                continue

            fresh.append((pub_time, item))

    fresh.sort(key=lambda x: x[0], reverse=True)
    return fresh

def google_company_feed(company):
    q = urllib.parse.quote_plus(f"{company} NSE stock")
    return f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"

# -------------------------------------------------
# LIVE MODE
# -------------------------------------------------
if st.session_state.live:

    start_time = time.time()

    with placeholder.container():
        st.subheader(f"Updated @ {datetime.utcnow().strftime('%H:%M:%S')} UTC")

        # -----------------------------
        # INDIA GENERAL
        # -----------------------------
        if "General" in news_type:
            fresh_news = process_sources(INDIA_GENERAL_SOURCES)

            if fresh_news:
                st.success(f"🔥 {len(fresh_news)} NEW updates")

                for pub_time, item in fresh_news:
                    st.session_state.seen_links.add(item.link)
                    st.markdown(f"### {item.title}")
                    st.write(f"🕒 {time_ago(pub_time)}")
                    st.markdown(f"[Open Article]({item.link})")
                    st.divider()
            else:
                st.warning("No NEW breaking news. Showing latest headlines.")
                for src in INDIA_GENERAL_SOURCES:
                    feed = feedparser.parse(src)
                    for item in feed.entries[:3]:
                        st.markdown(f"### {item.title}")
                        st.markdown(f"[Open Article]({item.link})")
                        st.divider()

            st.session_state.last_check = datetime.now(timezone.utc)

        # -----------------------------
        # INDIA MARKET (NSE / BSE)
        # -----------------------------
        else:
            tab_nse, tab_bse = st.tabs(["📊 NSE", "🏦 BSE"])

            # -------- NSE TAB --------
            with tab_nse:
                company = st.selectbox(
                    "Filter NSE news by company (optional)",
                    ["All Companies"] + NSE_COMPANIES
                )

                sources = list(NSE_BASE_SOURCES)

                if company != "All Companies":
                    sources.append(google_company_feed(company))

                fresh_news = process_sources(
                    sources,
                    None if company == "All Companies" else company
                )

                if fresh_news:
                    for pub_time, item in fresh_news:
                        st.session_state.seen_links.add(item.link)
                        st.markdown(f"### {item.title}")
                        st.write(f"🕒 {time_ago(pub_time)}")
                        st.markdown(f"[Open Article]({item.link})")
                        st.divider()
                else:
                    st.info("No NEW NSE updates")

            # -------- BSE TAB --------
            with tab_bse:
                fresh_news = process_sources(BSE_SOURCES)

                if fresh_news:
                    for pub_time, item in fresh_news:
                        st.session_state.seen_links.add(item.link)
                        st.markdown(f"### {item.title}")
                        st.write(f"🕒 {time_ago(pub_time)}")
                        st.markdown(f"[Open Article]({item.link})")
                        st.divider()
                else:
                    st.info("No NEW BSE updates")

            st.session_state.last_check = datetime.now(timezone.utc)

    elapsed = int(time.time() - start_time)
    remaining = max(refresh_interval - elapsed, 0)

    st.write(f"⏳ Next refresh in **{remaining}s**")

    time.sleep(remaining)
    st.rerun()

else:
    st.info("Click 🚀 Start Live Updates to begin streaming news.")
