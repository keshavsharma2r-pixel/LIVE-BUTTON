import streamlit as st
import feedparser
from datetime import datetime, date
from zoneinfo import ZoneInfo
import socket
import urllib.parse
import time
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------ CONFIG ------------------
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")
socket.setdefaulttimeout(5)  # Reduced timeout for faster loading

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
if "settings" not in st.session_state:
    st.session_state.settings = {
        "view_mode": "list",
        "sentiment_analysis": True,
    }

# ------------------ PROFESSIONAL CSS ------------------
st.markdown("""
<style>
    .stApp {
        background: #0a0e1a;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%);
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(30, 58, 138, 0.4);
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .header-title {
        font-size: 32px;
        font-weight: 800;
        color: white;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .header-subtitle {
        font-size: 14px;
        color: rgba(255,255,255,0.7);
        margin-top: 4px;
        font-weight: 500;
    }
    
    .live-badge {
        background: #dc2626;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 12px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        animation: pulse-badge 2s infinite;
    }
    
    @keyframes pulse-badge {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    .live-dot {
        width: 6px;
        height: 6px;
        background: white;
        border-radius: 50%;
        animation: blink-dot 1s infinite;
    }
    
    @keyframes blink-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    
    .stat-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(59, 130, 246, 0.15);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        transition: all 0.2s ease;
    }
    
    .stat-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
    }
    
    .stat-number {
        font-size: 28px;
        font-weight: 800;
        color: #3b82f6;
        margin: 8px 0;
    }
    
    .stat-label {
        font-size: 11px;
        color: rgba(255,255,255,0.6);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    .article-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(59, 130, 246, 0.15);
        border-left: 3px solid #3b82f6;
        padding: 20px 24px;
        margin-bottom: 16px;
        transition: all 0.2s ease;
        border-radius: 8px;
    }
    
    .article-card:hover {
        border-left-color: #60a5fa;
        border-color: rgba(59, 130, 246, 0.3);
        transform: translateX(4px);
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.1);
    }
    
    .article-title {
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 12px;
        line-height: 1.5;
    }
    
    .article-meta {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }
    
    .badge {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    
    .badge-source {
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .badge-category {
        background: rgba(139, 92, 246, 0.15);
        color: #a78bfa;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    
    .badge-time {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .badge-live {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
        animation: pulse-badge 2s infinite;
    }
    
    .badge-sentiment-positive {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .badge-sentiment-negative {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .badge-sentiment-neutral {
        background: rgba(148, 163, 184, 0.15);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.3);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 700;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 12px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    .stTextInput > div > div > input {
        background: #1e293b;
        border: 1px solid rgba(59, 130, 246, 0.2);
        color: white;
        border-radius: 8px;
        padding: 10px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: rgba(59, 130, 246, 0.5);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #1e293b;
        padding: 6px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        color: rgba(255,255,255,0.6);
        font-weight: 700;
        padding: 10px 20px;
        font-size: 13px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        color: white;
    }
    
    .compact-row {
        background: #1e293b;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 8px;
        border-left: 2px solid #3b82f6;
        transition: all 0.2s ease;
    }
    
    .compact-row:hover {
        background: #334155;
        transform: translateX(4px);
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0f172a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #3b82f6;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 class="header-title">📰 NEWS PRO</h1>
            <p class="header-subtitle">Real-time aggregation • Auto-refresh • Enterprise grade</p>
        </div>
        <div class="live-badge">
            <div class="live-dot"></div>
            LIVE
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------ STATS ------------------
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Articles</div>
        <div class="stat-number">{len(st.session_state.seen)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Read</div>
        <div class="stat-number" style="color: #4ade80;">{len(st.session_state.read_articles)}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Saved</div>
        <div class="stat-number" style="color: #fbbf24;">{len(st.session_state.bookmarks)}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    read_rate = int((len(st.session_state.read_articles) / max(len(st.session_state.seen), 1)) * 100)
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Read Rate</div>
        <div class="stat-number" style="color: #a78bfa;">{read_rate}%</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    last_update = st.session_state.last_fetch.strftime("%H:%M:%S") if st.session_state.last_fetch else "--:--:--"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Updated</div>
        <div class="stat-number" style="font-size: 20px;">{last_update}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------ QUICK ACTIONS ------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔖 BOOKMARKS", use_container_width=True):
        st.session_state.show_bookmarks = not st.session_state.get("show_bookmarks", False)

with col2:
    if st.button("🔥 TRENDING", use_container_width=True):
        st.session_state.show_trends = not st.session_state.get("show_trends", False)

with col3:
    view_modes = {"list": "📋 LIST", "compact": "📄 COMPACT"}
    current_mode = st.session_state.settings["view_mode"]
    next_mode = "compact" if current_mode == "list" else "list"
    if st.button(view_modes[current_mode], use_container_width=True):
        st.session_state.settings["view_mode"] = next_mode
        st.rerun()

with col4:
    if st.button("🔄 REFRESH", use_container_width=True):
        st.session_state.seen.clear()
        st.session_state.last_fetch = None
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ------------------ FILTERS ------------------
f1, f2, f3 = st.columns([5, 2, 1])

with f1:
    search_input = st.text_input(
        "🔍 Search",
        placeholder="Keywords, company, topic...",
        value=st.session_state.search_query,
        label_visibility="collapsed"
    )

with f2:
    date_input = st.date_input("📅", value=st.session_state.filter_date, label_visibility="collapsed")

with f3:
    if st.button("APPLY", use_container_width=True):
        st.session_state.search_query = search_input.strip()
        st.session_state.filter_date = date_input
        st.session_state.seen.clear()
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ------------------ UTILITY FUNCTIONS (OPTIMIZED) ------------------
@st.cache_data(ttl=45)  # Cache for 45 seconds
def fetch_feed(url):
    try:
        return feedparser.parse(url, request_headers={'User-Agent': 'Mozilla/5.0'})
    except:
        return None

def fetch_all_feeds_parallel(urls):
    """Fetch multiple feeds in parallel for speed"""
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_feed, url): url for url in urls}
        for future in as_completed(future_to_url):
            try:
                result = future.result()
                if result and result.entries:
                    results.append(result)
            except:
                pass
    return results

def get_source(entry):
    try:
        domain = urllib.parse.urlparse(entry.link).netloc.replace("www.", "")
        return domain.split('.')[0].upper()
    except:
        return "UNKNOWN"

def categorize_article(title, summary=""):
    text = f"{title} {summary}".lower()
    categories = {
        "Politics": ["election", "government", "minister", "parliament", "president"],
        "Technology": ["tech", "ai", "software", "app", "digital", "cyber"],
        "Business": ["business", "company", "market", "stock", "economy", "trade"],
        "Sports": ["cricket", "football", "match", "player", "tournament", "game"],
        "Health": ["health", "medical", "vaccine", "disease", "hospital"],
    }
    for category, keywords in categories.items():
        if any(kw in text for kw in keywords):
            return category
    return "General"

def analyze_sentiment(title, summary=""):
    text = f"{title} {summary}".lower()
    positive = ["success", "win", "growth", "up", "gain", "boost", "surge", "record"]
    negative = ["crisis", "fail", "decline", "down", "loss", "crash", "threat", "collapse"]
    pos = sum(1 for w in positive if w in text)
    neg = sum(1 for w in negative if w in text)
    if pos > neg:
        return "🟢 Positive", "badge-sentiment-positive"
    elif neg > pos:
        return "🔴 Negative", "badge-sentiment-negative"
    return "⚪ Neutral", "badge-sentiment-neutral"

def freshness_label(pub_time):
    delta = datetime.now(IST) - pub_time
    minutes = int(delta.total_seconds() / 60)
    if minutes <= 15:
        return "LIVE", f"{minutes}m", "badge-live"
    elif minutes <= 120:
        return "RECENT", f"{minutes//60}h", "badge-time"
    return "OLDER", f"{minutes//60}h", "badge-time"

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
]

# ------------------ BOOKMARKS VIEW ------------------
if st.session_state.get("show_bookmarks", False):
    st.markdown("## 🔖 Bookmarks")
    if not st.session_state.bookmarks:
        st.info("📭 No bookmarks yet")
    else:
        for link, data in st.session_state.bookmarks.items():
            st.markdown(f"""
            <div class="article-card">
                <div class="article-title">{data['title']}</div>
                <span class="badge badge-time">Saved: {data['saved_at']}</span>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns([5, 1])
            with col1:
                st.link_button("🔗 Open", link, use_container_width=True)
            with col2:
                if st.button("🗑️", key=f"del_{link}"):
                    del st.session_state.bookmarks[link]
                    st.rerun()
    st.stop()

# ------------------ TRENDING VIEW ------------------
if st.session_state.get("show_trends", False):
    st.markdown("## 🔥 Trending")
    st.info("🚀 Trending analysis coming soon")
    st.stop()

# ------------------ RENDER NEWS (OPTIMIZED) ------------------
def render_news(feeds, tab_name):
    REFRESH = 45  # Faster refresh - 45 seconds
    now = datetime.now(IST)
    
    # Auto-refresh logic
    if st.session_state.last_fetch:
        elapsed = (now - st.session_state.last_fetch).total_seconds()
        if elapsed < REFRESH:
            time.sleep(3)
            st.rerun()
    
    st.session_state.last_fetch = now
    
    # Fetch all feeds in parallel (MUCH FASTER)
    feed_results = fetch_all_feeds_parallel(feeds)
    
    collected = []
    
    for feed in feed_results:
        for e in feed.entries[:15]:  # Limit to 15 per feed for speed
            try:
                if hasattr(e, 'published_parsed'):
                    pub_utc = datetime(*e.published_parsed[:6], tzinfo=UTC)
                else:
                    continue
                pub_ist = pub_utc.astimezone(IST)
            except:
                continue
            
            title = e.title
            summary = getattr(e, 'summary', '')
            
            # Filters
            if st.session_state.search_query:
                text = f"{title} {summary}".lower()
                if st.session_state.search_query.lower() not in text:
                    continue
            
            if st.session_state.filter_date:
                if pub_ist.date() != st.session_state.filter_date:
                    continue
            
            if e.link in st.session_state.seen:
                continue
            
            st.session_state.seen.add(e.link)
            
            sentiment, sentiment_class = analyze_sentiment(title, summary)
            
            collected.append({
                'time': pub_ist,
                'title': title,
                'link': e.link,
                'source': get_source(e),
                'summary': summary,
                'category': categorize_article(title, summary),
                'sentiment': sentiment,
                'sentiment_class': sentiment_class,
                'is_read': e.link in st.session_state.read_articles,
                'is_bookmarked': e.link in st.session_state.bookmarks
            })
    
    collected.sort(key=lambda x: x['time'], reverse=True)
    
    if not collected:
        st.info("📭 No new articles")
        time.sleep(REFRESH)
        st.rerun()
        return
    
    st.success(f"✨ {len(collected)} articles")
    
    # Render based on view mode
    view_mode = st.session_state.settings["view_mode"]
    
    if view_mode == "compact":
        for article in collected:
            render_compact(article)
    else:
        for article in collected:
            render_full(article)
    
    time.sleep(REFRESH)
    st.rerun()

def render_full(a):
    tag, age, tag_class = freshness_label(a['time'])
    
    st.markdown(f"""
    <div class="article-card">
        <div class="article-title">{a['title']}</div>
        <div class="article-meta">
            <span class="badge badge-source">📰 {a['source']}</span>
            <span class="badge badge-category">{a['category']}</span>
            <span class="badge {tag_class}">{tag} • {age}</span>
            <span class="badge {a['sentiment_class']}">{a['sentiment']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if a['summary']:
        with st.expander("📄 Preview", expanded=False):
            st.write(a['summary'][:250] + "...")
    
    col1, col2, col3 = st.columns(3)
    icon = "🔖" if a['is_bookmarked'] else "📑"
    
    with col1:
        if st.button("✓ Read", key=f"r_{a['link']}", use_container_width=True):
            st.session_state.read_articles.add(a['link'])
            st.rerun()
    with col2:
        if st.button(f"{icon} Save", key=f"b_{a['link']}", use_container_width=True):
            if a['is_bookmarked']:
                del st.session_state.bookmarks[a['link']]
            else:
                st.session_state.bookmarks[a['link']] = {
                    'title': a['title'],
                    'saved_at': datetime.now(IST).strftime("%Y-%m-%d %H:%M")
                }
            st.rerun()
    with col3:
        st.link_button("🔗 Open", a['link'], use_container_width=True)

def render_compact(a):
    tag, age, _ = freshness_label(a['time'])
    read = "✓" if a['is_read'] else ""
    bookmark = "🔖" if a['is_bookmarked'] else ""
    
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown(f"""
        <div class="compact-row">
            {read} {bookmark} <strong style="color: white;">{a['title']}</strong><br>
            <small style="color: #64748b;">{tag} {age} • {a['source']} • {a['category']}</small>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.link_button("Open", a['link'], use_container_width=True, key=f"o_{a['link']}")

# ------------------ TABS ------------------
tabs = st.tabs(["🌍 Global", "🇮🇳 India", "📈 Markets"])

with tabs[0]:
    render_news(GLOBAL_FEEDS, "Global")

with tabs[1]:
    render_news(INDIA_FEEDS, "India")

with tabs[2]:
    render_news(MARKET_FEEDS, "Markets")
