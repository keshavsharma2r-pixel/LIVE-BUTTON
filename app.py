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
import base64

# ------------------ TIMEZONE ------------------
IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")
socket.setdefaulttimeout(10)

# ------------------ PAGE CONFIG ------------------
st.set_page_config(layout="wide", page_title="NEWS PRO", page_icon="📰")

# ------------------ INITIALIZE STORAGE ------------------
async def init_storage():
    try:
        bookmarks = await window.storage.get('bookmarks')
        if bookmarks:
            st.session_state.bookmarks = json.loads(bookmarks['value'])
        
        custom_feeds = await window.storage.get('custom_feeds')
        if custom_feeds:
            st.session_state.custom_feeds = json.loads(custom_feeds['value'])
            
        settings = await window.storage.get('settings')
        if settings:
            st.session_state.settings = json.loads(settings['value'])
    except:
        pass

# ------------------ SESSION STATE ------------------
if "live" not in st.session_state:
    st.session_state.live = False
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
        "dark_mode": False,
        "show_images": True,
        "view_mode": "list",
        "auto_summarize": False,
        "sentiment_analysis": True,
        "exclude_keywords": [],
        "priority_sources": []
    }
if "selected_categories" not in st.session_state:
    st.session_state.selected_categories = []
if "selected_sources" not in st.session_state:
    st.session_state.selected_sources = []

# ------------------ DARK MODE CSS ------------------
def apply_theme():
    if st.session_state.settings["dark_mode"]:
        st.markdown("""
        <style>
        .stApp {
            background-color: #1a1a1a;
            color: #ffffff;
        }
        .stMarkdown, .stText {
            color: #ffffff;
        }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# ------------------ HEADER ------------------
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📰 NEWS PRO")
with col2:
    if st.button("⚙️ Settings"):
        st.session_state.show_settings = not st.session_state.get("show_settings", False)

# ------------------ SETTINGS SIDEBAR ------------------
if st.session_state.get("show_settings", False):
    with st.sidebar:
        st.header("⚙️ Settings")
        
        st.subheader("🎨 Appearance")
        dark = st.checkbox("Dark Mode", value=st.session_state.settings["dark_mode"])
        if dark != st.session_state.settings["dark_mode"]:
            st.session_state.settings["dark_mode"] = dark
            st.rerun()
        
        st.session_state.settings["show_images"] = st.checkbox(
            "Show Images", 
            value=st.session_state.settings["show_images"]
        )
        
        st.session_state.settings["view_mode"] = st.radio(
            "View Mode",
            ["list", "compact", "cards"],
            index=["list", "compact", "cards"].index(st.session_state.settings["view_mode"])
        )
        
        st.divider()
        
        st.subheader("🤖 AI Features")
        st.session_state.settings["auto_summarize"] = st.checkbox(
            "Auto Summarize (requires API)",
            value=st.session_state.settings["auto_summarize"]
        )
        st.session_state.settings["sentiment_analysis"] = st.checkbox(
            "Sentiment Analysis",
            value=st.session_state.settings["sentiment_analysis"]
        )
        
        st.divider()
        
        st.subheader("📡 Custom Feeds")
        new_feed = st.text_input("Add RSS Feed URL")
        if st.button("➕ Add Feed"):
            if new_feed and new_feed not in st.session_state.custom_feeds:
                st.session_state.custom_feeds.append(new_feed)
                st.success("Feed added!")
                st.rerun()
        
        if st.session_state.custom_feeds:
            st.write("**Your Feeds:**")
            for idx, feed in enumerate(st.session_state.custom_feeds):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(feed[:40] + "...")
                with col2:
                    if st.button("🗑️", key=f"del_{idx}"):
                        st.session_state.custom_feeds.pop(idx)
                        st.rerun()
        
        st.divider()
        
        st.subheader("🚫 Exclude Keywords")
        exclude_input = st.text_input("Keywords to exclude (comma-separated)")
        if st.button("Save Exclusions"):
            keywords = [k.strip().lower() for k in exclude_input.split(",") if k.strip()]
            st.session_state.settings["exclude_keywords"] = keywords
            st.success("Exclusions saved!")

# ------------------ CONTROLS ------------------
col1, col2, col3, col4 = st.columns([4, 1, 1, 1])

with col2:
    if st.button("🔴 LIVE", use_container_width=True):
        st.session_state.live = True
        st.session_state.seen.clear()
        st.session_state.last_fetch = None
        st.rerun()

with col3:
    if st.button("⏹ STOP", use_container_width=True):
        st.session_state.live = False
        st.rerun()

with col4:
    if st.button("🔖 Saved", use_container_width=True):
        st.session_state.show_bookmarks = not st.session_state.get("show_bookmarks", False)

st.divider()

# ------------------ FILTERS ------------------
f1, f2, f3, f4, f5 = st.columns([4, 2, 1.5, 1.5, 1.5])

with f1:
    search_input = st.text_input(
        "🔍 Search",
        placeholder="Keywords, company, topic...",
        value=st.session_state.search_query
    )

with f2:
    date_input = st.date_input(
        "📅 Date",
        value=st.session_state.filter_date
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

with f5:
    if st.button("📊 Stats", use_container_width=True):
        st.session_state.show_stats = not st.session_state.get("show_stats", False)

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

# ------------------ STATUS ------------------
status1, status2, status3 = st.columns(3)

with status1:
    if st.session_state.live:
        st.markdown(
            "<div style='background:#ef4444;color:white;padding:8px;border-radius:8px;"
            "text-align:center;font-weight:bold;'>🔴 LIVE</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='background:#64748b;color:white;padding:8px;border-radius:8px;"
            "text-align:center;font-weight:bold;'>⏹ STOPPED</div>",
            unsafe_allow_html=True
        )

with status2:
    if st.session_state.last_fetch:
        st.info(f"🕐 {st.session_state.last_fetch.strftime('%I:%M:%S %p')}")

with status3:
    st.success(f"📚 {len(st.session_state.read_articles)} Read | 🔖 {len(st.session_state.bookmarks)} Saved")

st.divider()

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
    
    positive = ["success", "win", "growth", "positive", "up", "gain", "boost", "surge"]
    negative = ["crisis", "fail", "decline", "negative", "down", "loss", "crash", "fall"]
    
    pos_count = sum(1 for word in positive if word in text)
    neg_count = sum(1 for word in negative if word in text)
    
    if pos_count > neg_count:
        return "🟢 Positive", "#10b981"
    elif neg_count > pos_count:
        return "🔴 Negative", "#ef4444"
    else:
        return "⚪ Neutral", "#6b7280"

def freshness_label(pub_time):
    delta = datetime.now(IST) - pub_time
    minutes = int(delta.total_seconds() / 60)
    
    if minutes < 0:
        return "🔵 JUST NOW", "now"
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
    st.header("🔖 Saved Articles")
    
    if not st.session_state.bookmarks:
        st.info("No bookmarks yet. Click the bookmark icon on any article to save it.")
    else:
        for link, data in st.session_state.bookmarks.items():
            with st.container():
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"### {data['title']}")
                    st.caption(f"Saved on: {data['saved_at']}")
                    if data.get('note'):
                        st.info(f"📝 Note: {data['note']}")
                with col2:
                    if st.button("🗑️", key=f"del_bm_{link}"):
                        del st.session_state.bookmarks[link]
                        st.rerun()
                
                st.markdown(f"[Open Article]({link})")
                st.divider()
    
    st.stop()

# ------------------ STATS VIEW ------------------
if st.session_state.get("show_stats", False):
    st.header("📊 Reading Statistics")
    
    stat1, stat2, stat3 = st.columns(3)
    with stat1:
        st.metric("Articles Read", len(st.session_state.read_articles))
    with stat2:
        st.metric("Bookmarks", len(st.session_state.bookmarks))
    with stat3:
        st.metric("Custom Feeds", len(st.session_state.custom_feeds))
    
    st.divider()
    st.info("More analytics coming soon: trending topics, reading time, favorite sources...")
    
    st.stop()

# ------------------ RENDER NEWS ------------------
def render_news(feeds, tab_name):
    FETCH_INTERVAL = 60
    now = datetime.now(IST)
    
    if st.session_state.live:
        if st.session_state.last_fetch:
            elapsed = (now - st.session_state.last_fetch).total_seconds()
            if elapsed < FETCH_INTERVAL:
                time.sleep(2)
                st.rerun()
                return
        st.session_state.last_fetch = now
    
    with st.spinner(f"Fetching {tab_name} news..."):
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
                
                # Exclude keywords
                if should_exclude(title, summary):
                    continue
                
                # Date filter
                if st.session_state.apply_filters and st.session_state.filter_date:
                    if pub_ist.date() != st.session_state.filter_date:
                        continue
                
                # Search filter
                if st.session_state.apply_filters and st.session_state.search_query:
                    text = f"{title} {summary}".lower()
                    if st.session_state.search_query.lower() not in text:
                        continue
                
                # Category filter
                category = categorize_article(title, summary)
                if st.session_state.selected_categories:
                    if category not in st.session_state.selected_categories:
                        continue
                
                # Source filter
                source = get_source(e)
                if st.session_state.selected_sources:
                    if source not in st.session_state.selected_sources:
                        continue
                
                # Skip duplicates
                if e.link in st.session_state.seen:
                    continue
                
                st.session_state.seen.add(e.link)
                
                sentiment, color = analyze_sentiment(title, summary) if st.session_state.settings["sentiment_analysis"] else ("", "")
                image = get_image(e) if st.session_state.settings["show_images"] else None
                
                collected.append({
                    'time': pub_ist,
                    'title': title,
                    'link': e.link,
                    'source': source,
                    'summary': summary,
                    'category': category,
                    'sentiment': sentiment,
                    'color': color,
                    'image': image,
                    'is_read': e.link in st.session_state.read_articles,
                    'is_bookmarked': e.link in st.session_state.bookmarks
                })
        
        collected.sort(key=lambda x: x['time'], reverse=True)
        
        if collected:
            st.success(f"📊 {len(collected)} articles found")
        else:
            if st.session_state.apply_filters:
                st.warning("🔍 No articles match your filters.")
            else:
                st.info("📭 No new articles.")
            return
        
        # Render based on view mode
        view_mode = st.session_state.settings["view_mode"]
        
        if view_mode == "cards":
            cols = st.columns(2)
            for idx, article in enumerate(collected):
                with cols[idx % 2]:
                    render_article_card(article)
        else:
            for article in collected:
                if view_mode == "compact":
                    render_article_compact(article)
                else:
                    render_article_list(article)
        
        if st.session_state.live:
            time.sleep(FETCH_INTERVAL)
            st.rerun()

def render_article_list(article):
    with st.container():
        # Header
        col1, col2, col3 = st.columns([6, 1, 1])
        
        with col1:
            read_style = "opacity: 0.6;" if article['is_read'] else ""
            st.markdown(f"<h3 style='{read_style}'>{article['title']}</h3>", unsafe_allow_html=True)
        
        with col2:
            bookmark_icon = "🔖" if article['is_bookmarked'] else "📑"
            if st.button(bookmark_icon, key=f"bm_{article['link']}"):
                if article['is_bookmarked']:
                    del st.session_state.bookmarks[article['link']]
                else:
                    st.session_state.bookmarks[article['link']] = {
                        'title': article['title'],
                        'saved_at': datetime.now(IST).strftime("%Y-%m-%d %H:%M"),
                        'note': ''
                    }
                st.rerun()
        
        with col3:
            if st.button("✓ Read", key=f"rd_{article['link']}"):
                st.session_state.read_articles.add(article['link'])
                st.rerun()
        
        # Image
        if article['image']:
            st.image(article['image'], use_container_width=True)
        
        # Meta info
        tag, age = freshness_label(article['time'])
        
        meta1, meta2, meta3 = st.columns(3)
        with meta1:
            st.markdown(
                f"<span style='background:#e5e7eb;padding:4px 10px;border-radius:6px;"
                f"font-size:13px;font-weight:600;'>📰 {article['source']}</span>",
                unsafe_allow_html=True
            )
        with meta2:
            st.write(f"{tag} • {age}")
        with meta3:
            st.markdown(
                f"<span style='background:#f3f4f6;padding:4px 10px;border-radius:6px;"
                f"font-size:12px;'>🏷️ {article['category']}</span>",
                unsafe_allow_html=True
            )
        
        if article['sentiment']:
            st.markdown(
                f"<span style='color:{article['color']};font-weight:600;'>{article['sentiment']}</span>",
                unsafe_allow_html=True
            )
        
        # Summary
        if article['summary']:
            with st.expander("📄 Preview"):
                st.write(article['summary'][:300] + "...")
        
        st.markdown(f"🔗 [Read Full Article]({article['link']})")
        st.divider()

def render_article_compact(article):
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col1:
        tag, age = freshness_label(article['time'])
        read_mark = "✓" if article['is_read'] else ""
        st.markdown(f"{read_mark} **{article['title']}** | {tag} {age} | {article['source']}")
    
    with col2:
        bookmark_icon = "🔖" if article['is_bookmarked'] else "📑"
        if st.button(bookmark_icon, key=f"bm_c_{article['link']}"):
            if article['is_bookmarked']:
                del st.session_state.bookmarks[article['link']]
            else:
                st.session_state.bookmarks[article['link']] = {
                    'title': article['title'],
                    'saved_at': datetime.now(IST).strftime("%Y-%m-%d %H:%M")
                }
            st.rerun()
    
    with col3:
        st.markdown(f"[Open]({article['link']})")

def render_article_card(article):
    with st.container():
        if article['image']:
            st.image(article['image'], use_container_width=True)
        
        st.markdown(f"### {article['title']}")
        
        tag, age = freshness_label(article['time'])
        st.caption(f"{tag} • {age} • {article['source']}")
        
        if article['sentiment']:
            st.markdown(f"**{article['sentiment']}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📖 Read", key=f"rd_card_{article['link']}", use_container_width=True):
                st.session_state.read_articles.add(article['link'])
                st.rerun()
        with col2:
            bookmark_icon = "🔖 Saved" if article['is_bookmarked'] else "📑 Save"
            if st.button(bookmark_icon, key=f"bm_card_{article['link']}", use_container_width=True):
                if article['is_bookmarked']:
                    del st.session_state.bookmarks[article['link']]
                else:
                    st.session_state.bookmarks[article['link']] = {
                        'title': article['title'],
                        'saved_at': datetime.now(IST).strftime("%Y-%m-%d %H:%M")
                    }
                st.rerun()
        
        st.markdown(f"[Read Article]({article['link']})")
        st.divider()

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
        render_news(st.session_state.custom_feeds, "Custom")
