import streamlit as st
import json
import time
import pandas as pd
from datetime import datetime
from scrape import (
    scrape_website,
    extract_body_content,
    extract_metadata,
    extract_structured_data,
    extract_article_content,
    clean_body_content,
    split_dom_content,
    scrape_multiple_urls,
)
from parse import parse_with_together, summarize_with_together

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NexScrape · AI Web Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Outfit:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Dark tech theme */
.stApp {
    background: #090c14;
    color: #e2e8f0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #1e2d45;
}

/* Main header */
.main-header {
    font-family: 'Space Mono', monospace;
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00d4ff 0%, #7b2ff7 50%, #ff6b6b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -2px;
    margin-bottom: 0;
}

.sub-header {
    color: #4a6fa5;
    font-size: 0.85rem;
    font-family: 'Space Mono', monospace;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 0;
}

/* Metric cards */
.metric-card {
    background: #0d1421;
    border: 1px solid #1e2d45;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.4rem 0;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #00d4ff44; }
.metric-label {
    color: #4a6fa5;
    font-size: 0.72rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-family: 'Space Mono', monospace;
}
.metric-value {
    color: #00d4ff;
    font-size: 1.6rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    letter-spacing: 1px;
}
.badge-success { background: #003322; color: #00ff88; border: 1px solid #00ff8844; }
.badge-info    { background: #001833; color: #00d4ff; border: 1px solid #00d4ff44; }
.badge-warn    { background: #332200; color: #ffaa00; border: 1px solid #ffaa0044; }

/* Section headers */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #4a6fa5;
    border-bottom: 1px solid #1e2d45;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem 0;
}

/* URL input styling */
.stTextInput input {
    background: #0d1421 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.85rem !important;
}
.stTextInput input:focus {
    border-color: #00d4ff !important;
    box-shadow: 0 0 0 2px #00d4ff22 !important;
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, #00d4ff22, #7b2ff722) !important;
    border: 1px solid #00d4ff66 !important;
    color: #00d4ff !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}
.stButton button:hover {
    background: linear-gradient(135deg, #00d4ff44, #7b2ff744) !important;
    border-color: #00d4ff !important;
    transform: translateY(-1px) !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #0d1421 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 8px !important;
    color: #8892a4 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 1px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0d1117;
    border-bottom: 1px solid #1e2d45;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    color: #4a6fa5;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 0.6rem 1.2rem;
}
.stTabs [aria-selected="true"] {
    color: #00d4ff !important;
    border-bottom: 2px solid #00d4ff !important;
}

/* Text areas */
.stTextArea textarea {
    background: #0d1421 !important;
    border: 1px solid #1e2d45 !important;
    color: #e2e8f0 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.78rem !important;
    border-radius: 8px !important;
}

/* Select box */
.stSelectbox > div > div {
    background: #0d1421 !important;
    border: 1px solid #1e2d45 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #090c14; }
::-webkit-scrollbar-thumb { background: #1e2d45; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #00d4ff44; }

/* Result box */
.result-box {
    background: #0d1421;
    border: 1px solid #1e2d45;
    border-left: 3px solid #00d4ff;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-family: 'Outfit', sans-serif;
    font-size: 0.9rem;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 500px;
    overflow-y: auto;
}

/* Info/success/error overrides */
.stAlert {
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.78rem !important;
}

/* Divider */
hr { border-color: #1e2d45 !important; margin: 1.5rem 0 !important; }

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0;'>
        <div style='font-family: Space Mono; font-size:1.4rem; color:#00d4ff;'>⚡ NEX</div>
        <div style='font-size:0.65rem; color:#4a6fa5; letter-spacing:4px;'>SCRAPE CONFIG</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="section-title">⚙ Scraper Settings</div>', unsafe_allow_html=True)
    force_selenium = st.toggle("Force Selenium (JS sites)", value=False)
    wait_time = st.slider("JS render wait (sec)", 1, 10, 3)
    aggressive_clean = st.toggle("Aggressive cleaning (articles)", value=True)
    chunk_size = st.select_slider("Chunk size", options=[3000, 4000, 6000, 8000, 10000], value=6000)

    st.divider()
    st.markdown('<div class="section-title">🧠 AI Settings</div>', unsafe_allow_html=True)
    ai_enabled = st.toggle("Enable AI Parsing", value=True)
    if not ai_enabled:
        st.caption("AI parsing disabled — raw extraction only")

    st.divider()
    st.markdown('<div class="section-title">📋 Batch Mode</div>', unsafe_allow_html=True)
    batch_urls_raw = st.text_area(
        "Batch URLs (one per line)",
        height=100,
        placeholder="https://example.com\nhttps://another.com",
        help="Scrape multiple URLs sequentially"
    )
    batch_delay = st.slider("Delay between requests (sec)", 0.5, 5.0, 1.5)

    if st.button("▶ RUN BATCH", use_container_width=True):
        urls = [u.strip() for u in batch_urls_raw.strip().splitlines() if u.strip()]
        if urls:
            with st.spinner(f"Scraping {len(urls)} URLs..."):
                results = scrape_multiple_urls(urls, delay=batch_delay)
                st.session_state.batch_results = results
                st.success(f"✓ {len(results)} URLs scraped")
        else:
            st.warning("Enter at least one URL")

    # Show batch results download
    if "batch_results" in st.session_state:
        data = [{
            "url": r.get("url",""),
            "method": r.get("method",""),
            "error": r.get("error",""),
            "text_preview": r.get("text","")[:300],
        } for r in st.session_state.batch_results]
        df = pd.DataFrame(data)
        st.download_button(
            "⬇ Download Batch CSV",
            df.to_csv(index=False),
            file_name="batch_results.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ─── Main Header ──────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_title:
    st.markdown('<h1 class="main-header">NexScrape</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">// AI-Powered Web Intelligence Engine</p>', unsafe_allow_html=True)

st.divider()

# ─── URL Input ────────────────────────────────────────────────────────────────
col_url, col_btn = st.columns([5, 1])
with col_url:
    url = st.text_input(
        "",
        placeholder="https://target-site.com",
        label_visibility="collapsed",
        key="url_input",
    )
with col_btn:
    scrape_btn = st.button("⚡ SCRAPE", use_container_width=True)

# ─── Scrape Execution ─────────────────────────────────────────────────────────
if scrape_btn:
    if not url:
        st.warning("Enter a URL first")
    else:
        with st.spinner("Initializing scrape sequence..."):
            progress = st.progress(0, text="Connecting...")
            time.sleep(0.3)
            progress.progress(20, text="Fetching page...")

            try:
                result = scrape_website(url, use_selenium=force_selenium, wait_time=wait_time)
                progress.progress(50, text="Extracting content...")
                html = result["html"]

                body = extract_body_content(html)
                cleaned = clean_body_content(body, aggressive=aggressive_clean)
                article = extract_article_content(html)
                metadata = extract_metadata(html, url)
                structured = extract_structured_data(html)

                progress.progress(80, text="Processing...")
                time.sleep(0.2)

                st.session_state.update({
                    "html": html,
                    "body": body,
                    "cleaned": cleaned,
                    "article": article,
                    "metadata": metadata,
                    "structured": structured,
                    "dom_chunks": split_dom_content(cleaned, chunk_size),
                    "scrape_result": result,
                    "url": url,
                })
                progress.progress(100, text="Done!")
                time.sleep(0.3)
                progress.empty()

            except Exception as e:
                progress.empty()
                st.error(f"Scrape failed: {e}")
                st.stop()

# ─── Results Dashboard ────────────────────────────────────────────────────────
if "scrape_result" in st.session_state:
    r = st.session_state.scrape_result
    meta = st.session_state.metadata
    chunks = st.session_state.dom_chunks

    # ── Stats Row ──
    st.markdown('<div class="section-title">📊 Scrape Intelligence Report</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Method</div>
            <div class="metric-value" style="font-size:1rem;">{r.get("method","—").upper()}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Load time</div>
            <div class="metric-value">{r.get("elapsed","—")}s</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Words</div>
            <div class="metric-value">{meta.get("word_count",0):,}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Links</div>
            <div class="metric-value">{len(meta.get("links",[]))}</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Images</div>
            <div class="metric-value">{len(meta.get("images",[]))}</div>
        </div>""", unsafe_allow_html=True)

    # ── Page Title / Description ──
    if meta.get("title"):
        st.markdown(f"""
        <div style='margin:1rem 0; padding:1rem 1.2rem;
             background:#0d1421; border:1px solid #1e2d45;
             border-radius:10px;'>
            <div style='color:#4a6fa5;font-size:0.7rem;letter-spacing:2px;font-family:Space Mono;'>PAGE TITLE</div>
            <div style='color:#e2e8f0;font-size:1.1rem;font-weight:600;margin-top:4px;'>{meta["title"]}</div>
            {f'<div style="color:#8892a4;font-size:0.85rem;margin-top:6px;">{meta["description"]}</div>' if meta.get("description") else ""}
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Tabs ──
    tab_content, tab_meta, tab_ai, tab_export = st.tabs([
        "📄  CONTENT",
        "🔍  METADATA",
        "🧠  AI PARSE",
        "⬇  EXPORT",
    ])

    # ── Tab: Content ──
    with tab_content:
        view_mode = st.radio(
            "View",
            ["Article Extract", "Cleaned Text", "Raw HTML"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if view_mode == "Article Extract":
            st.markdown('<div class="section-title">▸ Smart Article Extraction</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="result-box">{st.session_state.article[:8000]}</div>', unsafe_allow_html=True)

        elif view_mode == "Cleaned Text":
            st.markdown('<div class="section-title">▸ Cleaned Text Content</div>', unsafe_allow_html=True)
            with st.expander(f"View cleaned content ({len(chunks)} chunk(s))", expanded=True):
                st.text_area("", st.session_state.cleaned[:10000], height=350,
                             label_visibility="collapsed")

        else:
            st.markdown('<div class="section-title">▸ Raw HTML</div>', unsafe_allow_html=True)
            with st.expander("Raw HTML source"):
                st.code(st.session_state.html[:20000], language="html")

        # Headings
        headings = meta.get("headings", {})
        if headings:
            st.markdown('<div class="section-title">▸ Page Structure</div>', unsafe_allow_html=True)
            for level, items in headings.items():
                indent = int(level[1:]) - 1
                for item in items[:8]:
                    color = ["#00d4ff","#7b2ff7","#ff6b6b","#ffaa00","#00ff88","#ff66cc"][int(level[1:])-1]
                    st.markdown(
                        f'<div style="padding-left:{indent*20}px;color:{color};'
                        f'font-family:Space Mono;font-size:0.8rem;margin:3px 0;">'
                        f'<span style="opacity:0.4">{level.upper()} </span>{item}</div>',
                        unsafe_allow_html=True
                    )

    # ── Tab: Metadata ──
    with tab_meta:
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.markdown('<div class="section-title">▸ SEO & Open Graph</div>', unsafe_allow_html=True)
            seo_data = {
                "Title": meta.get("title",""),
                "Description": meta.get("description",""),
                "Keywords": meta.get("keywords",""),
                "Language": meta.get("language",""),
                "Canonical": meta.get("canonical",""),
            }
            for k, v in seo_data.items():
                if v:
                    st.markdown(f"""
                    <div style='margin-bottom:0.6rem;'>
                        <span style='color:#4a6fa5;font-size:0.7rem;font-family:Space Mono;
                        letter-spacing:1px;text-transform:uppercase;'>{k}</span><br>
                        <span style='color:#e2e8f0;font-size:0.85rem;'>{v[:200]}</span>
                    </div>""", unsafe_allow_html=True)

            og = meta.get("og", {})
            if og:
                st.markdown('<div class="section-title">▸ Open Graph Tags</div>', unsafe_allow_html=True)
                for k, v in og.items():
                    st.markdown(f'<span class="badge badge-info">og:{k}</span> '
                               f'<span style="font-size:0.82rem;color:#c8d0dc;">{str(v)[:100]}</span><br>',
                               unsafe_allow_html=True)

        with col_m2:
            st.markdown('<div class="section-title">▸ Discovered Contacts</div>', unsafe_allow_html=True)
            emails = meta.get("emails", [])
            phones = meta.get("phone_numbers", [])

            if emails:
                st.markdown("**Emails found:**")
                for e in emails[:10]:
                    st.markdown(f'<span class="badge badge-success">✉ {e}</span><br>',
                               unsafe_allow_html=True)
            if phones:
                st.markdown("**Phone numbers:**")
                for p in phones[:5]:
                    st.markdown(f'<span class="badge badge-warn">📞 {p}</span><br>',
                               unsafe_allow_html=True)
            if not emails and not phones:
                st.caption("No contact info detected")

            # Social links
            socials = list(set(meta.get("social_links", [])))
            if socials:
                st.markdown('<div class="section-title">▸ Social Links</div>', unsafe_allow_html=True)
                for s in socials[:10]:
                    st.markdown(f'<a href="{s}" style="color:#7b2ff7;font-size:0.8rem;'
                               f'font-family:Space Mono;display:block;margin:3px 0;" '
                               f'target="_blank">{s[:60]}</a>', unsafe_allow_html=True)

        # Images table
        images = meta.get("images", [])
        if images:
            st.markdown('<div class="section-title">▸ Images Detected</div>', unsafe_allow_html=True)
            df_imgs = pd.DataFrame(images[:50])
            st.dataframe(df_imgs, use_container_width=True, hide_index=True)

        # Structured data / tables
        tables = st.session_state.structured.get("tables", [])
        if tables:
            st.markdown('<div class="section-title">▸ Page Tables</div>', unsafe_allow_html=True)
            for i, table in enumerate(tables[:3]):
                with st.expander(f"Table {i+1} ({len(table)} rows)"):
                    try:
                        st.dataframe(pd.DataFrame(table), use_container_width=True)
                    except:
                        st.json(table)

        json_ld = st.session_state.structured.get("json_ld", [])
        if json_ld:
            st.markdown('<div class="section-title">▸ JSON-LD Structured Data</div>', unsafe_allow_html=True)
            with st.expander("JSON-LD"):
                st.json(json_ld)

    # ── Tab: AI Parse ──
    with tab_ai:
        if not ai_enabled:
            st.info("Enable AI Parsing in the sidebar to use this feature.")
        else:
            st.markdown('<div class="section-title">🧠 AI Extraction Engine</div>', unsafe_allow_html=True)

            col_q1, col_q2 = st.columns(2)
            with col_q1:
                # Quick presets
                preset = st.selectbox("Quick presets", [
                    "Custom query...",
                    "Extract all prices and product names",
                    "Get all article headlines",
                    "Extract contact information",
                    "List all links and their anchor text",
                    "Extract company name, address, and hours",
                    "Get all dates and events mentioned",
                    "Extract review scores and sentiments",
                    "Pull job titles and company names",
                ])
            with col_q2:
                ai_mode = st.radio("Mode", ["Extract", "Summarize"], horizontal=True)

            parse_description = ""
            if preset == "Custom query..." or ai_mode == "Summarize":
                parse_description = st.text_area(
                    "Describe what to extract" if ai_mode == "Extract" else "Summarization notes (optional)",
                    height=80,
                    placeholder="e.g. Extract all product names with their prices and ratings...",
                )
            else:
                parse_description = preset
                st.info(f"Preset: **{preset}**")

            col_parse_btn, col_clear_btn = st.columns([3, 1])
            with col_parse_btn:
                parse_btn = st.button("🧠 RUN AI ANALYSIS", use_container_width=True)
            with col_clear_btn:
                if st.button("CLEAR", use_container_width=True):
                    st.session_state.pop("ai_result", None)
                    st.rerun()

            if parse_btn:
                if ai_mode == "Summarize":
                    with st.spinner("Generating intelligent summary..."):
                        try:
                            result_text = summarize_with_together(chunks)
                            st.session_state.ai_result = result_text
                        except Exception as e:
                            st.error(f"AI error: {e}")
                else:
                    if not parse_description:
                        st.warning("Describe what to extract or choose a preset")
                    else:
                        with st.spinner(f"Analyzing {len(chunks)} chunk(s)..."):
                            progress2 = st.progress(0)
                            try:
                                result_text = parse_with_together(chunks, parse_description)
                                progress2.progress(100)
                                progress2.empty()
                                st.session_state.ai_result = result_text
                            except Exception as e:
                                progress2.empty()
                                st.error(f"AI error: {e}")

            if "ai_result" in st.session_state:
                st.markdown('<div class="section-title">▸ AI Analysis Result</div>',
                           unsafe_allow_html=True)
                st.markdown(f'<div class="result-box">{st.session_state.ai_result}</div>',
                           unsafe_allow_html=True)
                st.download_button(
                    "⬇ Download Result",
                    st.session_state.ai_result,
                    file_name="ai_extract.txt",
                    mime="text/plain",
                )

    # ── Tab: Export ──
    with tab_export:
        st.markdown('<div class="section-title">⬇ Export Scraped Data</div>', unsafe_allow_html=True)
        col_e1, col_e2, col_e3 = st.columns(3)

        with col_e1:
            st.download_button(
                "📄 Cleaned Text (.txt)",
                st.session_state.cleaned,
                file_name=f"scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with col_e2:
            meta_export = {
                "url": st.session_state.url,
                "scraped_at": st.session_state.scrape_result.get("timestamp"),
                "method": st.session_state.scrape_result.get("method"),
                "metadata": meta,
                "structured_data": st.session_state.structured,
            }
            st.download_button(
                "🔍 Metadata (.json)",
                json.dumps(meta_export, indent=2, ensure_ascii=False),
                file_name=f"metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )

        with col_e3:
            if meta.get("links"):
                df_links = pd.DataFrame(meta["links"])
                st.download_button(
                    "🔗 All Links (.csv)",
                    df_links.to_csv(index=False),
                    file_name=f"links_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        # Full HTML download
        st.markdown('<div class="section-title">▸ Raw Exports</div>', unsafe_allow_html=True)
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            st.download_button(
                "🌐 Full HTML Source",
                st.session_state.html,
                file_name=f"page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True,
            )
        with col_h2:
            st.download_button(
                "📰 Article Extract (.txt)",
                st.session_state.article,
                file_name=f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # Images export
        if meta.get("images"):
            st.markdown('<div class="section-title">▸ Images List</div>', unsafe_allow_html=True)
            df_img_export = pd.DataFrame(meta["images"])
            st.download_button(
                "🖼 Images List (.csv)",
                df_img_export.to_csv(index=False),
                file_name=f"images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
