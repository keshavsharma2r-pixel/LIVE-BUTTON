import streamlit as st
import feedparser
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import socket
import urllib.parse
import time
import json
import re
from collections import Counter

# ------------------ TIMEZONE ------------------
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")
socket.setdefaulttimeout(10)

# ------------------ PAGE CONFIG ------------------
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
if "apply_filters" not in st.session_state:
    st.session_state.apply_filters = False
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "filter_date" not in st.session_state:
    st.session_state.filter_date = None
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = {}
if "read_articles" not in st.session_state:
    st.session_state.read_articles = set()
if "custom_feeds" not in st.session_state:
    st.session_state.custom_feeds = []
if "settings" not in st.session_state:
    st.session_state.settings = {
        "dark_mode": True,
        "show_images": True,
        "view_mode": "cards",
        "sentiment_analysis": True,
        "exclude_keywords": [],
        "alert_keywords": [],
        "auto_refresh": True
    }
if "selected_categories" not in st.session_state:
    st.session_state.selected_categories = []
if "selected_sources" not in st.session_state:
    st.session_state.selected_sources = []

# ------------------ MODERN DARK THEME CSS ------------------
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom header styling */
    .main-header {
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        padding: 20px 30px;
        border-radius: 16px;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .header-title {
        font-size: 42px;
        font-weight: 800;
        color: white;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        font-size: 16px;
        color: rgba(255,255,255,0.9);
        margin-top: 5px;
    }
    
    /* Stats cards */
    .stat-card {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    }
    
    .stat-number {
        font-size: 32px;
        font-weight: 700;
        color: #60a5fa;
        margin: 10px 0;
    }
    
    .stat-label {
        font-size: 14px;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Live indicator */
    .live-badge {
        background: #ef4444;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: white;
        border-radius: 50%;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    
    /* Filter section */
    .filter-section {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    
    /* Article cards */
    .article-card {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    }
    
    .article-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(96, 165, 250, 0.3);
        border-color: rgba(96, 165, 250, 0.5);
    }
    
    .article-title {
        font-size: 22px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 12px;
        line-height: 1.4;
    }
    
    .article-meta {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 16px;
    }
    
    .badge {
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .badge-source {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
    }
    
    .badge-category {
        background: rgba(167, 139, 250, 0.2);
        color: #c4b5fd;
        border: 1px solid rgba(167, 139, 250, 0.3);
    }
    
    .badge-time {
        background: rgba(34, 197, 94, 0.2);
        color: #86efac;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .badge-alert {
        background: #ef4444;
        color: white;
        animation: pulse 2s infinite;
    }
    
    /* Sentiment badges */
    .sentiment-positive {
        background: rgba(34, 197, 94, 0.2);
        color: #86efac;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .sentiment-negative {
        background: rgba(239, 68, 68, 0.2);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .sentiment-neutral {
        background: rgba(148, 163, 184, 0.2);
        color: #cbd5e1;
        border: 1px solid rgba(148, 163, 184, 0.3);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255,255,255,0.1);
        color: white;
        border-radius: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(30, 41, 59, 0.6);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: rgba(255,255,255,0.7);
        font-weight: 600;
        padding: 12px 24px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(30, 41, 59, 0.5);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(59, 130, 246, 0.5);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(59, 130, 246, 0.7);
    }
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 class="header-title">📰 NEWS PRO</h1>
            <p class="header-subtitle">Real-time news aggregation from trusted sources worldwide</p>
        </div>
        <div class="live-badge">
            <div class="live-dot"></div>
            LIVE
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------ STATS BAR ------------------
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Articles Today</div>
        <div class="stat-number">{len(st.session_state.seen)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Read</div>
        <div class="stat-number" style="color: #34d399;">{len(st.session_state.read_articles)}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Bookmarked</div>
        <div class="stat-number" style="color: #fbbf24;">{len(st.session_state.bookmarks)}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Custom Feeds</div>
        <div class="stat-number" style="color: #a78bfa;">{len(st.session_state.custom_feeds)}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    last_update = st.session_state.last_fetch.strftime("%H:%M:%S") if st.session_state.last_fetch else "Never"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Last Update</div>
        <div class="stat-number" style="color: #60a5fa; font-size: 20px;">{last_update}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------ QUICK ACTIONS ------------------
action_col1, action_col2, action_col3, action_col4, action_col5 = st.columns(5)

with action_col1:
    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.show_settings = not st.session_state.get("show_settings", False)

with action_col2:
    if st.button("🔖 Bookmarks", use_container_width=True):
        st.session_state.show_bookmarks = not st.session_state.get("show_bookmarks", False)

with action_col3:
    if st.button("🔥 Trending", use_container_width=True):
        st.session_state.show_trends = not st.session_state.get("show_trends", False)

with action_col4:
    if st.button("📊 Analytics", use_container_width=True):
        st.session_state.show_stats = not st.session_state.get("show_stats", False)

with action_col5:
    export_menu = st.selectbox("📤 Export", ["None", "CSV", "JSON"], key="export_select", label_visibility="collapsed")
    if export_menu != "None":
        st.session_state.export_format = export_menu

# ------------------ SETTINGS SIDEBAR ------------------
if st.session_state.get("show_settings", False):
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        st.markdown("#### 🎨 Appearance")
        st.session_state.settings["show_images"] = st.checkbox(
            "Show Images", 
            value=st.session_state.settings["show_images"]
        )
        
        st.session_state.settings["view_mode"] = st.radio(
            "View Mode",
            ["cards", "list", "compact"],
            index=["cards", "list", "compact"].index(st.session_state.settings["view_mode"])
        )
        
        st.divider()
        
        st.markdown("#### 🤖 Features")
        st.session_state.settings["sentiment_analysis"] = st.checkbox(
            "Sentiment Analysis",
            value=st.session_state.settings["sentiment_analysis"]
        )
        
        st.divider()
        
        st.markdown("#### 📡 Custom Feeds")
        new_feed = st.text_input("Add RSS Feed URL")
        if st.button("➕ Add Feed"):
            if new_feed and new_feed not in st.session_state.custom_feeds:
                st.session_state.custom_feeds.append(new_feed)
                st.success("Feed added!")
                st.rerun()
        
        if st.session_state.custom_feeds:
            for idx, feed in enumerate(st.session_state.custom_feeds):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(feed[:30] + "...")
                with col2:
                    if st.button("🗑️", key=f"del_{idx}"):
                        st.session_state.custom_feeds.pop(idx)
                        st.rerun()
        
        st.divider()
        
        st.markdown("#### 🚫 Filters")
        exclude_input = st.text_input("Exclude Keywords (comma-separated)")
        if st.button("Save Exclusions"):
            keywords = [k.strip().lower() for k in exclude_input.split(",") if k.strip()]
            st.session_state.settings["exclude_keywords"] = keywords
            st.success("Saved!")
        
        st.divider()
        
        st.markdown("#### 🔔 Alerts")
        alert_input = st.text_input("Alert Keywords (comma-separated)")
        if st.button("Save Alerts"):
            keywords = [k.strip().lower() for k in alert_input.split(",") if k.strip()]
            st.session_state.settings["alert_keywords"] = keywords
            st.success("Alerts saved!")

# ------------------ FILTERS ------------------
st.markdown('<div class="filter-section">', unsafe_allow_html=True)

f1, f2, f3, f4 = st.columns([4, 2, 1, 1])

with f1:
    search_input = st.text_input(
        "🔍 Search",
        placeholder="Keywords, company, topic...",
        value=st.session_state.search_query,
        label_visibility="collapsed"
    )

with f2:
    date_input = st.date_input(
        "📅 Date",
        value=st.session_state.filter_date,
        label_visibility="collapsed"
    )

with f3:
    if st.button("🔍 Apply", use_container_width=True):
        st.session_state.search_query = search_input.strip()
        st.session_state.filter_date = date_input
        st.session_state.apply_filters = bool(search_input.strip() or date_input)
        st.session_state.seen.clear()
        st.rerun()

with f4:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.apply_filters = False
        st.session_state.search_query = ""
        st.session_state.filter_date = None
        st.session_state.selected_categories = []
        st.session_state.selected_sources = []
        st.session_state.seen.clear()
        st.rerun()

# Advanced filters
with st.expander("🎯 Advanced Filters"):
    adv1, adv2 = st.columns(2)
    
    with adv1:
        categories = ["Politics", "Technology", "Business", "Sports", "Entertainment", "Health", "Science"]
        st.session_state.selected_categories = st.multiselect(
            "Categories",
            categories,
            default=st.session_state.selected_categories
        )
    
    with adv2:
        sources = ["REUTERS", "BBC", "GOOGLE", "NDTV", "ECONOMICTIMES", "MONEYCONTROL"]
        st.session_state.selected_sources = st.multiselect(
            "Sources",
            sources,
            default=st.session_state.selected_sources
        )

st.markdown('</div>', unsafe_allow_html=True)

# ------------------ UTILITY FUNCTIONS ------------------
@st.cache_data(ttl=60)
def fetch_feed(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        return feedparser.parse(url, request_headers=headers)
    except:
        return None

def get_source(entry):
    try:
        domain = urllib.parse.urlparse(entry.link).netloc.replace("www.", "")
        return domain.split('.')[0].upper()
    except:
        return "UNKNOWN"

def get_image(entry):
    try:
        if hasattr(entry, 'media_content') and entry.media_content:
            return entry.media_content[0].get('url')
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            return entry.media_thumbnail[0].get('url')
        if hasattr(entry, 'enclosures') and entry.enclosures:
            return entry.enclosures[0].get('href')
    except:
        pass
    return None

def categorize_article(title, summary=""):
    text = f"{title} {summary}".lower()
    
    categories = {
        "Politics": ["election", "government", "minister", "parliament", "politics", "vote"],
        "Technology": ["tech", "ai", "software", "app", "digital", "cyber", "data"],
        "Business": ["business", "company", "ceo", "market", "stock", "economy"],
        "Sports": ["cricket", "football", "match", "player", "tournament", "game"],
        "Entertainment": ["movie", "film", "music", "celebrity", "actor", "entertainment"],
        "Health": ["health", "medical", "doctor", "hospital", "disease", "vaccine"],
        "Science": ["science", "research", "study", "discovery", "scientist"]
    }
    
    for category, keywords in categories.items():
        if any(kw in text for kw in keywords):
            return category
    return "General"

def analyze_sentiment(title, summary=""):
    text = f"{title} {summary}".lower()
    
    positive = ["success", "win", "growth", "positive", "up", "gain", "boost", "surge", "breakthrough"]
    negative = ["crisis", "fail", "decline", "negative", "down", "loss", "crash", "fall", "threat"]
    
    pos_count = sum(1 for word in positive if word in text)
    neg_count = sum(1 for word in negative if word in text)
    
    if pos_count > neg_count:
        return "🟢 Positive", "sentiment-positive"
    elif neg_count > pos_count:
        return "🔴 Negative", "sentiment-negative"
    else:
        return "⚪ Neutral", "sentiment-neutral"

def freshness_label(pub_time):
    delta = datetime.now(IST) - pub_time
    minutes = int(delta.total_seconds() / 60)
    
    if minutes < 0:
        return "🔵 NOW", "now"
    elif minutes <= 15:
        return "🟢 LIVE", f"{minutes}m"
    elif minutes <= 120:
        return "🟡 RECENT", f"{minutes//60}h {minutes%60}m"
    elif minutes <= 1440:
        return "⚪ TODAY", f"{minutes//60}h"
    else:
        return "⚫ OLD", f"{minutes//1440}d"

def should_exclude(title, summary=""):
    text = f"{title} {summary}".lower()
    exclude = st.session_state.settings["exclude_keywords"]
    return any(kw in text for kw in exclude)

def extract_keywords(articles):
    text = " ".join([a['title'] for a in articles]).lower()
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
    words = re.findall(r'\b[a-z]{4,}\b', text)
    words = [w for w in words if w not in stop_words]
    return Counter(words).most_common(15)

def export_to_csv(articles):
    import io
    output = io.StringIO()
    output.write("Title,Source,Category,Sentiment,Time,Link\n")
    for a in articles:
        output.write(f'"{a["title"]}",{a["source"]},{a["category"]},{a["sentiment"]},{a["time"]},{a["link"]}\n')
    return output.getvalue()

def export_to_json(articles):
    data = [{
        'title': a['title'],
        'source': a['source'],
        'category': a['category'],
        'sentiment': a['sentiment'],
        'time': str(a['time']),
        'link': a['link']
    } for a in articles]
    return json.dumps(data, indent=2)

# ------------------ FEEDS ------------------
GLOBAL_FEEDS = [
    "https://news.google.com/rss",
    "https://www.reuters.com/rssFeed/worldNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
]

INDIA_FEEDS = [
    "https://news.google.com/rss/search?q=India",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
]

MARKET_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://www.livemint.com/rss/markets",
]

# ------------------ BOOKMARKS VIEW ------------------
if st.session_state.get("show_bookmarks", False):
    st.markdown("## 🔖 Saved Articles")
    
    if not st.session_state.bookmarks:
        st.info("No bookmarks yet. Click the bookmark icon on any article to save it.")
    else:
        for link, data in st.session_state.bookmarks.items():
            st.markdown(f"""
            <div class="article-card">
                <div class="article-title">{data['title']}</div>
                <div class="article-meta">
                    <span class="badge badge-time">Saved: {data['saved_at']}</span>
                </div>
                <a href="{link}" target="_blank" style="color: #60a5fa;">🔗 Open Article</a>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🗑️ Remove", key=f"del_bm_{link}"):
                del st.session_state.bookmarks[link]
                st.rerun()
    
    st.stop()

# ------------------ STATS VIEW ------------------
if st.session_state.get("show_stats", False):
    st.markdown("## 📊 Analytics Dashboard")
    
    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        st.metric("Total Articles", len(st.session_state.seen))
    with stat2:
        st.metric("Articles Read", len(st.session_state.read_articles))
    with stat3:
        st.metric("Bookmarks", len(st.session_state.bookmarks))
    with stat4:
        read_rate = int((len(st.session_state.read_articles) / max(len(st.session_state.seen), 1)) * 100)
        st.metric("Read Rate", f"{read_rate}%")
    
    st.info("📈 More analytics coming soon: reading trends, category breakdown, source analysis...")
    st.stop()

# ------------------ TRENDING TOPICS ------------------
if st.session_state.get("show_trends", False):
    st.markdown("## 🔥 Trending Topics")
    st.caption("Most mentioned keywords across all articles")
    
    all_articles = []
    for feeds in [GLOBAL_FEEDS, INDIA_FEEDS, MARKET_FEEDS]:
        for url in feeds:
            feed = fetch_feed(url)
            if feed and feed.entries:
                for e in feed.entries[:50]:
                    all_articles.append({'title': e.title})
    
    if all_articles:
        keywords = extract_keywords(all_articles)
        
        cols = st.columns(5)
        for idx, (word, count) in enumerate(keywords):
            with cols[idx % 5]:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                            color:white;padding:16px;border-radius:12px;text-align:center;margin:5px;'>
                    <div style='font-size:20px;font-weight:700;'>{word.upper()}</div>
                    <div style='font-size:14px;opacity:0.9;'>{count} mentions</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No articles available for trend analysis")
    
    if st.button("← Back"):
        st.session_state.show_trends = False
        st.rerun()
    
    st.stop()

# ------------------ RENDER NEWS ------------------
def render_news(feeds, tab_name):
    FETCH_INTERVAL = 60
    now = datetime.now(IST)
    
    # Auto-refresh logic
    if st.session_state.last_fetch:
        elapsed = (now - st.session_state.last_fetch).total_seconds()
        if elapsed < FETCH_INTERVAL:
            time.sleep(2)
            st.rerun()
    
    st.session_state.last_fetch = now
    
    with st.spinner(f"🔄 Fetching latest {tab_name} news..."):
        collected = []
        
        for url in feeds:
            feed = fetch_feed(url)
            if not feed or not feed.entries:
                continue
            
            for e in feed.entries:
                try:
                    if hasattr(e, 'published_parsed') and e.published_parsed:
                        pub_utc = datetime(*e.published_parsed[:6], tzinfo=UTC)
                    elif hasattr(e, 'updated_parsed') and e.updated_parsed:
                        pub_utc = datetime(*e.updated_parsed[:6], tzinfo=UTC)
                    else:
                        continue
                    
                    pub_ist = pub_utc.astimezone(IST)
                except:
                    continue
                
                title = e.title
                summary = getattr(e, 'summary', '')
                
                if should_exclude(title, summary):
                    continue
                
                if st.session_state.apply_filters and st.session_state.search_query:
                    text = f"{title} {summary}".lower()
                    if st.session_state.search_query.lower() not in text:
                        continue
                
                category = categorize_article(title, summary)
                if st.session_state.selected_categories:
                    if category not in st.session_state.selected_categories:
                        continue
                
                source = get_source(e)
                if st.session_state.selected_sources:
                    if source not in st.session_state.selected_sources:
                        continue
                
                if e.link in st.session_state.seen:
                    continue
                
                st.session_state.seen.add(e.link)
                
                sentiment, sentiment_class = analyze_sentiment(title, summary) if st.session_state.settings["sentiment_analysis"] else ("", "")
                image = get_image(e) if st.session_state.settings["show_images"] else None
                
                is_alert = False
                if st.session_state.settings["alert_keywords"]:
                    text = f"{title} {summary}".lower()
                    is_alert = any(kw in text for kw in st.session_state.settings["alert_keywords"])
                
                collected.append({
                    'time': pub_ist,
                    'title': title,
                    'link': e.link,
                    'source': source,
                    'summary': summary,
                    'category': category,
                    'sentiment': sentiment,
                    'sentiment_class': sentiment_class,
                    'image': image,
                    'is_read': e.link in st.session_state.read_articles,
                    'is_bookmarked': e.link in st.session_state.bookmarks,
                    'is_alert': is_alert
                })
        
        collected.sort(key=lambda x: x['time'], reverse=True)
        
        # Handle export
        if st.session_state.get("export_format"):
            export_format = st.session_state.export_format
            
            if export_format == "CSV":
                csv_data = export_to_csv(collected)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"news_{tab_name}_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            elif export_format == "JSON":
                json_data = export_to_json(collected)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"news_{tab_name}_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            st.session_state.export_format = None
        
        if collected:
            st.success(f"✨ {len(collected)} articles found")
        else:
            if st.session_state.apply_filters:
                st.warning("🔍 No articles match your filters.")
            else:
                st.info("📭 No new articles at this moment.")
            return
        
        # Render articles
        view_mode = st.session_state.settings["view_mode"]
        
        if view_mode == "cards":
            cols = st.columns(2)
            for idx, article in enumerate(collected):
                with cols[idx % 2]:
                    render_article_card(article)
        elif view_mode == "compact":
            for article in collected:
                render_article_compact(article)
        else:
            for article in collected:
                render_article_full(article)
    
    # Auto-refresh
    time.sleep(FETCH_INTERVAL)
    st.rerun()

def render_article_card(article):
    alert_badge = '<span class="badge badge-alert">🔔 ALERT</span>' if article.get('is_alert') else ''
    
    tag, age = freshness_label(article['time'])
    
    sentiment_badge = f'<span class="badge {article["sentiment_class"]}">{article["sentiment"]}</span>' if article['sentiment'] else ''
    
    image_html = f'<img src="{article["image"]}" style="width:100%; height:200px; object-fit:cover; border-radius:12px; margin-bottom:16px;">' if article['image'] else ''
    
    read_opacity = "opacity: 0.6;" if article['is_read'] else ""
    bookmark_icon = "🔖" if article['is_bookmarked'] else "📑"
    
    st.markdown(f"""
    <div class="article-card" style="{read_opacity}">
        {alert_badge}
        {image_html}
        <div class="article-title">{article['title']}</div>
        <div class="article-meta">
            <span class="badge badge-source">📰 {article['source']}</span>
            <span class="badge badge-category">🏷️ {article['category']}</span>
            <span class="badge badge-time">{tag} {age}</span>
            {sentiment_badge}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📖 Read", key=f"rd_{article['link']}", use_container_width=True):
            st.session_state.read_articles.add(article['link'])
            st.rerun()
    with col2:
        if st.button(f"{bookmark_icon} Save", key=f"bm_{article['link']}", use_container_width=True):
            if article['is_bookmarked']:
                del st.session_state.bookmarks[article['link']]
            else:
                st.session_state.bookmarks[article['link']] = {
                    'title': article['title'],
                    'saved_at': datetime.now(IST).strftime("%Y-%m-%d %H:%M")
                }
            st.rerun()
    with col3:
        st.link_button("🔗 Open", article['link'], use_container_width=True)

def render_article_full(article):
    alert_badge = '<span class="badge badge-alert">🔔 KEYWORD ALERT</span>' if article.get('is_alert') else ''
    
    tag, age = freshness_label(article['time'])
    sentiment_badge = f'<span class="badge {article["sentiment_class"]}">{article["sentiment"]}</span>' if article['sentiment'] else ''
    
    image_html = f'<img src="{article["image"]}" style="width:100%; max-height:400px; object-fit:cover; border-radius:12px; margin:16px 0;">' if article['image'] else ''
    
    read_opacity = "opacity: 0.6;" if article['is_read'] else ""
    
    st.markdown(f"""
    <div class="article-card" style="{read_opacity}">
        {alert_badge}
        <div class="article-title">{article['title']}</div>
        {image_html}
        <div class="article-meta">
            <span class="badge badge-source">📰 {article['source']}</span>
            <span class="badge badge-category">🏷️ {article['category']}</span>
            <span class="badge badge-time">{tag} • {age}</span>
            {sentiment_badge}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if article['summary']:
        with st.expander("📄 Preview"):
            st.write(article['summary'][:400] + "...")
    
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    bookmark_icon = "🔖" if article['is_bookmarked'] else "📑"
    
    with action_col1:
        if st.button("✓ Mark Read", key=f"rd_full_{article['link']}", use_container_width=True):
            st.session_state.read_articles.add(article['link'])
            st.rerun()
    
    with action_col2:
        if st.button(f"{bookmark_icon} Bookmark", key=f"bm_full_{article['link']}", use_container_width=True):
            if article['is_bookmarked']:
                del st.session_state.bookmarks[article['link']]
            else:
                st.session_state.bookmarks[article['link']] = {
                    'title': article['title'],
                    'saved_at': datetime.now(IST).strftime("%Y-%m-%d %H:%M")
                }
            st.rerun()
    
    with action_col3:
        share_text = urllib.parse.quote(f"{article['title']} {article['link']}")
        whatsapp_url = f"https://wa.me/?text={share_text}"
        st.link_button("📱 Share", whatsapp_url, use_container_width=True)
    
    with action_col4:
        st.link_button("🔗 Read Full", article['link'], use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

def render_article_compact(article):
    alert = "🔔" if article.get('is_alert') else ""
    read_mark = "✓" if article['is_read'] else ""
    bookmark_mark = "🔖" if article['is_bookmarked'] else ""
    
    tag, age = freshness_label(article['time'])
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        st.markdown(f"""
        <div style='padding: 12px; background: rgba(30, 41, 59, 0.5); border-radius: 8px; margin-bottom: 8px;'>
            {alert} {read_mark} {bookmark_mark} <strong>{article['title']}</strong><br>
            <small style='color: #94a3b8;'>{tag} {age} • {article['source']} • {article['category']}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.link_button("Open", article['link'], use_container_width=True, key=f"open_{article['link']}")

# ------------------ TABS ------------------
tabs_list = ["🌍 Global", "🇮🇳 India", "📈 Markets"]
if st.session_state.custom_feeds:
    tabs_list.append("📡 Custom")

tabs = st.tabs(tabs_list)

with tabs[0]:
    render_news(GLOBAL_FEEDS, "Global")

with tabs[1]:
    render_news(INDIA_FEEDS, "India")

with tabs[2]:
    render_news(MARKET_FEEDS, "Markets")

if st.session_state.custom_feeds and len(tabs) > 3:
    with tabs[3]:
        render_news(st.session_state.custom_feeds, "Custom")apply_filters and st.session_state.filter_date:
                    if pub_ist.date() != st.session_state.filter_date:
                        continue
                
                if st.session_
