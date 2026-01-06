import asyncio
import sys
import os

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
from analyzer import HybridAnalyzer
from scraper import EnterpriseScraper

st.set_page_config(page_title="InstaGuard Mobile Forensics", layout="wide")
st.title("📱 InstaGuard Mobile Forensics")
st.caption("Emulated iPhone 13 Pro Environment | Cyber Cell Standard")

@st.cache_resource
def load_engine():
    return HybridAnalyzer()

try:
    engine = load_engine()
    st.success(f"Database Loaded: {len(engine.toxic_phrases)} active threat patterns.")
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# Inputs
with st.container(border=True):
    c1, c2 = st.columns([4, 1])
    with c1:
        url = st.text_input("Target URL", placeholder="https://www.instagram.com/p/...")
    with c2:
        limit = st.number_input("Limit", 10, 500, 50)

if st.button("Start Mobile Extraction", type="primary"):
    if not url:
        st.warning("Enter URL")
        st.stop()

    bot = EnterpriseScraper()
    
    with st.status("Initializing iOS Environment...", expanded=True) as status:
        st.write(" Booting iPhone 13 Pro Emulator...")
        st.write("Simulating Touch Gestures...")
        st.write("Scanning Database Matches...")
        
        data = bot.run(url, limit, engine)
        status.update(label="Extraction Complete", state="complete", expanded=False)

    if data:
        st.error(f"Detected {len(data)} Compromised Comments")
        
        for i, item in enumerate(data):
            with st.container(border=True):
                st.subheader(f"Evidence Item #{i+1}")
                
                # Layout: Image (Left) | Data (Right)
                # Since mobile shots are tall, we give the image column less width
                c_img, c_data = st.columns([1, 2])
                
                with c_img:
                    if item['image'] and os.path.exists(item['image']):
                        # Set width to emulate phone screen size on dashboard
                        st.image(item['image'], caption="Mobile View Evidence", width=300)
                    else:
                        st.warning("No Image")
                
                with c_data:
                    st.markdown("### Threat Details")
                    st.info(item['text'])
                    st.markdown(f"**Detection Logic:** `{item['reason']}`")
                    st.divider()
                    st.caption("Note: Direct comment links are limited in Mobile Web mode.")
                    st.link_button("🔗 Open Post", item['link'])
    else:
        st.success(" No threats detected in this session.")