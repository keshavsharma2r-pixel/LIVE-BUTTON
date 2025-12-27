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

# ------------------ CONFIG ------------------
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")
socket.setdefaulttimeout(10)

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
        "show_images": True,
        "view_mode": "cards",
        "sentiment_analysis": True,
    }

# ------------------ MODERN CSS ------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main-header {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 40px rgba(59, 130, 246, 0.3);
    }
    
    .header-title {
        font-size: 48px;
        font-weight: 900;
        color: white;
        margin: 0;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        font-size: 18px;
        color: rgba(255,255,255,0.9);
        margin-top: 10px;
    }
    
    .live-badge {
        background: #ef4444;
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: 700;
        font-size: 16px;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        animation: pulse-badge 2s infinite;
    }
    
    @keyframes pulse-badge {
        0%, 100% { transform: scale(1); box-shadow: 0 0 20px rgba(239, 68, 68, 0.5); }
        50% { transform: scale(1.05); box-shadow: 0 0 30px rgba(239, 68, 68, 0.8); }
    }
    
    .live-dot {
        width: 10px;
        height: 10px;
        background: white;
        border-radius: 50%;
        animation: blink-dot 1s infinite;
    }
    
    @keyframes blink-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    
    .stat-card {
        background: rgba(30, 41, 59, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 25px;
        border-radius: 16px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        border-color: rgba(59, 130, 246, 0.6);
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
    }
    
    .stat-number {
        font-size: 36px;
        font-weight: 800;
        color: #60a5fa;
        margin: 10px 0;
    }
    
    .stat-label {
        font-size: 13px;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    
    .article-card {
        background: rgba(30, 41, 59, 0.95);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 25px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .article-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 40px rgba(59, 130, 246, 0.4);
        border-color: rgba(59, 130, 246, 0.6);
    }
    
    .article-title {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 15px;
        line-height: 1.4;
    }
    
    .badge {
        padding: 8px 14px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
        margin-right: 8px;
    }
    
    .badge-source {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
    }
    
    .badge-category {
        background: rgba(139, 92, 246, 0.3);
        color: #c4b5fd;
        border: 1px solid rgba(139, 92, 246, 0.5);
    }
    
    .badge-time {
        background: rgba(34, 197, 94, 0.3);
        color: #86efac;
        border: 1px solid rgba(34, 197, 94, 0.5);
    }
    
    .badge-alert {
        background: #ef4444;
        color: white;
        animation: pulse-badge 2s infinite;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 700;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.5);
    }
    
    .stTextInput > div > div > input {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: white;
        border-radius: 12px;
        padding: 12px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: rgba(59, 130, 246, 0.8);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 class="header-title">📰 NEWS PRO</h1>
            <p class="header-subtitle">Real-time news aggregation • Always live • Auto-refreshing</p>
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
        <div class="stat-label">📊 Articles</div>
        <div class="stat-number">{len(st.session_state.seen)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">✓ Read</div>
        <div class="stat-number" style="color: #34d399;">{len(st.session_state.read_articles)}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">🔖 Saved</div>
        <div class="stat-number" style="color: #fbbf24;">{len(st.session_state.bookmarks)}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    read_rate = int((len(st.session_state.read_articles) / max(len(st.session_state.seen), 1)) * 100)
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">📈 Read Rate</div>
        <div class="stat-number" style="color: #a78bfa;">{read_rate}%</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    last_update = st.session_state.last_fetch.strftime("%H:%M:%S") if st.session_state.last_fetch else "--:--:--"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">🕐 Updated</div>
        <div class="stat-number" style="color: #60a5fa; font-size: 22px;">{last_update}</div>
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
    view_modes = {"cards": "🎴 CARDS", "list": "📋 LIST", "compact": "📄 COMPACT"}
    current_mode = st.session_state.settings["view_mode"]
    next_mode = {"cards": "list", "list": "compact", "compact": "cards"}[current_mode]
    if st.button(view_modes[current_mode], use_container_width=True):
        st.session_state.settings["view_mode"] = next_mode
        st.rerun()

with col4:
    if st.button("🔄 REFRESH NOW", use_container_width=True):
        st.session_state.seen.clear()
        st.session_state.last_fetch = None
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ------------------ FILTERS ------------------
f1, f2, f3 = st.columns([5, 2, 1])

with f1:
    search_input = st.text_input(
        "🔍 Search articles...",
        placeholder="Keywords, company, topic...",
        value=st.session_state.search_query
    )

with f2:
    date_input = st.date_input("📅 Filter by date", value=st.session_state.filter_date)

with f3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 APPLY", use_container_width=True):
        st.session_state.search_query = search_input.strip()
        st.session_state.filter_date = date_input
        st.session_state.seen.clear()
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ------------------ UTILITY FUNCTIONS ------------------
@st.cache_data(ttl=60)
def fetch_feed(url):
    try:
        return feedparser.parse(url, request_headers={'User-Agent': 'Mozilla/5.0'})
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
    except:
        pass
    return None

def categorize_article(title, summary=""):
    text = f"{title} {summary}".lower()
    categories = {
        "Politics": ["election", "government", "minister", "parliament"],
        "Technology": ["tech", "ai", "software", "app", "digital"],
        "Business": ["business", "company", "market", "stock"],
        "Sports": ["cricket", "football", "match", "player"],
    }
    for category, keywords in categories.items():
        if any(kw in text for kw in keywords):
            return category
    return "General"

def analyze_sentiment(title, summary=""):
    text = f"{title} {summary}".lower()
    positive = ["success", "win", "growth", "up", "gain", "boost"]
    negative = ["crisis", "fail", "decline", "down", "loss", "crash"]
    pos_count = sum(1 for word in positive if word in text)
    neg_count = sum(1 for word in negative if word in text)
    if pos_count > neg_count:
        return "🟢 Positive"
    elif neg_count > pos_count:
        return "🔴 Negative"
    return "⚪ Neutral"

def freshness_label(pub_time):
    delta = datetime.now(IST) - pub_time
    minutes = int(delta.total_seconds() / 60)
    if minutes <= 15:
        return "🟢 LIVE", f"{minutes}m ago"
    elif minutes <= 120:
        return "🟡 RECENT", f"{minutes//60}h ago"
    return "⚪ OLDER", f"{minutes//60}h ago"

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
    st.markdown("## 🔖 Your Bookmarks")
    if not st.session_state.bookmarks:
        st.info("📭 No bookmarks yet. Start saving articles!")
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
                st.link_button("🔗 Open Article", link, use_container_width=True)
            with col2:
                if st.button("🗑️", key=f"del_{link}"):
                    del st.session_state.bookmarks[link]
                    st.rerun()
    st.stop()

# ------------------ TRENDING VIEW ------------------
if st.session_state.get("show_trends", False):
    st.markdown("## 🔥 Trending Topics")
    st.info("🚀 Trending analysis shows most mentioned keywords across all feeds")
    st.stop()

# ------------------ RENDER NEWS ------------------
def render_news(feeds, tab_name):
    REFRESH = 60
    now = datetime.now(IST)
    
    # Auto-refresh
    if st.session_state.last_fetch:
        elapsed = (now - st.session_state.last_fetch).total_seconds()
        if elapsed < REFRESH:
            time.sleep(2)
            st.rerun()
    
    st.session_state.last_fetch = now
    
    with st.spinner(f"🔄 Loading {tab_name} news..."):
        collected = []
        
        for url in feeds:
            feed = fetch_feed(url)
            if not feed or not feed.entries:
                continue
            
            for e in feed.entries:
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
                
                # Search filter
                if st.session_state.search_query:
                    text = f"{title} {summary}".lower()
                    if st.session_state.search_query.lower() not in text:
                        continue
                
                # Date filter
                if st.session_state.filter_date:
                    if pub_ist.date() != st.session_state.filter_date:
                        continue
                
                if e.link in st.session_state.seen:
                    continue
                
                st.session_state.seen.add(e.link)
                
                collected.append({
                    'time': pub_ist,
                    'title': title,
                    'link': e.link,
                    'source': get_source(e),
                    'summary': summary,
                    'category': categorize_article(title, summary),
                    'sentiment': analyze_sentiment(title, summary),
                    'image': get_image(e),
                    'is_read': e.link in st.session_state.read_articles,
                    'is_bookmarked': e.link in st.session_state.bookmarks
                })
        
        collected.sort(key=lambda x: x['time'], reverse=True)
        
        if not collected:
            st.info("📭 No articles at this moment. Refreshing soon...")
            time.sleep(REFRESH)
            st.rerun()
            return
        
        st.success(f"✨ Found {len(collected)} articles")
        
        # Render
        view_mode = st.session_state.settings["view_mode"]
        
        if view_mode == "cards":
            cols = st.columns(2)
            for idx, article in enumerate(collected):
                with cols[idx % 2]:
                    render_card(article)
        elif view_mode == "compact":
            for article in collected:
                render_compact(article)
        else:
            for article in collected:
                render_full(article)
    
    time.sleep(REFRESH)
    st.rerun()

def render_card(a):
    tag, age = freshness_label(a['time'])
    img_html = f'<img src="{a["image"]}" style="width:100%;height:180px;object-fit:cover;border-radius:12px;margin-bottom:12px;">' if a['image'] else ''
    
    st.markdown(f"""
    <div class="article-card">
        {img_html}
        <div class="article-title">{a['title']}</div>
        <span class="badge badge-source">{a['source']}</span>
        <span class="badge badge-category">{a['category']}</span>
        <span class="badge badge-time">{tag} {age}</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✓", key=f"r_{a['link']}", use_container_width=True):
            st.session_state.read_articles.add(a['link'])
            st.rerun()
    with col2:
        icon = "🔖" if a['is_bookmarked'] else "📑"
        if st.button(icon, key=f"b_{a['link']}", use_container_width=True):
            if a['is_bookmarked']:
                del st.session_state.bookmarks[a['link']]
            else:
                st.session_state.bookmarks[a['link']] = {
                    'title': a['title'],
                    'saved_at': datetime.now(IST).strftime("%Y-%m-%d %H:%M")
                }
            st.rerun()
    with col3:
        st.link_button("🔗", a['link'], use_container_width=True)

def render_full(a):
    tag, age = freshness_label(a['time'])
    img_html = f'<img src="{a["image"]}" style="width:100%;max-height:300px;object-fit:cover;border-radius:12px;margin:12px 0;">' if a['image'] else ''
    
    st.markdown(f"""
    <div class="article-card">
        <div class="article-title">{a['title']}</div>
        {img_html}
        <span class="badge badge-source">{a['source']}</span>
        <span class="badge badge-category">{a['category']}</span>
        <span class="badge badge-time">{tag} {age}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if a['summary']:
        with st.expander("📄 Preview"):
            st.write(a['summary'][:300] + "...")
    
    col1, col2, col3 = st.columns(3)
    icon = "🔖" if a['is_bookmarked'] else "📑"
    
    with col1:
        if st.button("✓ Read", key=f"rf_{a['link']}", use_container_width=True):
            st.session_state.read_articles.add(a['link'])
            st.rerun()
    with col2:
        if st.button(f"{icon} Save", key=f"bf_{a['link']}", use_container_width=True):
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
    tag, age = freshness_label(a['time'])
    read = "✓" if a['is_read'] else ""
    bookmark = "🔖" if a['is_bookmarked'] else ""
    
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown(f"""
        <div style='background:rgba(30,41,59,0.6);padding:15px;border-radius:10px;margin-bottom:10px;'>
            {read} {bookmark} <strong>{a['title']}</strong><br>
            <small style='color:#94a3b8;'>{tag} {age} • {a['source']}</small>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.link_button("Open", a['link'], use_container_width=True, key=f"oc_{a['link']}")

# ------------------ TABS ------------------
tabs = st.tabs(["🌍 Global", "🇮🇳 India", "📈 Markets"])

with tabs[0]:
    render_news(GLOBAL_FEEDS, "Global")

with tabs[1]:
    render_news(INDIA_FEEDS, "India")

with tabs[2]:
    render_news(MARKET_FEEDS, "Markets")
