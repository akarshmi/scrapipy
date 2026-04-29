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
from parse import parse_with_gemini, summarize_with_gemini

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Scrapipy",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Typography + Design System ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Syne:wght@400;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background: #f5f2ec;
    color: #1a1a1a;
}

.stApp { background: #f5f2ec; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #1a1a1a !important;
    border-right: none;
}
section[data-testid="stSidebar"] * {
    color: #c8c0b0 !important;
}
section[data-testid="stSidebar"] .stTextArea textarea,
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #2a2a2a !important;
    border-color: #3a3a3a !important;
    color: #c8c0b0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
}
section[data-testid="stSidebar"] .stSlider > div { filter: invert(0.85); }

/* ── Wordmark ── */
.wordmark {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 3.8rem;
    letter-spacing: -4px;
    color: #1a1a1a;
    line-height: 1;
    margin-bottom: 0;
}
.wordmark span {
    color: #c84b2f;
}
.tagline {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 3px;
    color: #888;
    text-transform: uppercase;
    margin-top: 6px;
}

/* ── URL bar ── */
.stTextInput input {
    background: #fff !important;
    border: 1.5px solid #1a1a1a !important;
    border-radius: 0 !important;
    color: #1a1a1a !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.9rem !important;
    padding: 0.7rem 1rem !important;
    transition: border-color 0.15s;
}
.stTextInput input:focus {
    border-color: #c84b2f !important;
    box-shadow: none !important;
}

/* ── Buttons ── */
.stButton button {
    background: #1a1a1a !important;
    color: #f5f2ec !important;
    border: none !important;
    border-radius: 0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    padding: 0.65rem 1.4rem !important;
    transition: background 0.15s !important;
}
.stButton button:hover {
    background: #c84b2f !important;
}

/* ── Stat cards ── */
.stat-row { display: flex; gap: 1px; margin: 1.5rem 0; background: #d4d0c8; }
.stat-card {
    background: #f5f2ec;
    flex: 1;
    padding: 1.2rem 1.4rem;
    border-bottom: 3px solid transparent;
    transition: border-color 0.2s;
}
.stat-card:hover { border-bottom-color: #c84b2f; }
.stat-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 2.5px;
    color: #888;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.stat-value {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.6rem;
    color: #1a1a1a;
    line-height: 1;
}

/* ── Section label ── */
.sec-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #888;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #d4d0c8;
    margin: 1.8rem 0 1rem;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #d4d0c8;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #888;
    padding: 0.7rem 1.4rem;
    background: transparent;
    border-radius: 0;
}
.stTabs [aria-selected="true"] {
    color: #1a1a1a !important;
    border-bottom: 2px solid #c84b2f !important;
    background: transparent !important;
}

/* ── Text areas ── */
.stTextArea textarea {
    background: #fff !important;
    border: 1.5px solid #d4d0c8 !important;
    border-radius: 0 !important;
    color: #1a1a1a !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
}
.stTextArea textarea:focus {
    border-color: #1a1a1a !important;
    box-shadow: none !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #fff !important;
    border: 1px solid #d4d0c8 !important;
    border-radius: 0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    color: #444 !important;
    letter-spacing: 1px !important;
}

/* ── Result display ── */
.result-block {
    background: #fff;
    border-left: 3px solid #c84b2f;
    padding: 1.2rem 1.4rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 480px;
    overflow-y: auto;
    color: #1a1a1a;
}

/* ── Page info card ── */
.page-card {
    background: #fff;
    border: 1px solid #d4d0c8;
    padding: 1.2rem 1.4rem;
    margin: 1rem 0;
}
.page-card-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 4px;
}
.page-card-desc {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: #666;
    line-height: 1.5;
}

/* ── Method badge ── */
.method-badge {
    display: inline-block;
    background: #1a1a1a;
    color: #f5f2ec;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 3px 10px;
}

/* ── Heading structure ── */
.heading-row {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    padding: 3px 0;
    color: #1a1a1a;
    border-bottom: 1px dashed #e8e4dc;
}
.heading-row .lvl { color: #c84b2f; margin-right: 6px; }

/* ── Selectbox ── */
.stSelectbox > div > div {
    border-radius: 0 !important;
    border-color: #d4d0c8 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
}

/* ── Radio ── */
.stRadio label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 1px !important;
}

/* ── Divider ── */
hr { border-color: #d4d0c8 !important; margin: 1.5rem 0 !important; }

/* ── Alerts ── */
.stAlert {
    border-radius: 0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #f5f2ec; }
::-webkit-scrollbar-thumb { background: #d4d0c8; }
::-webkit-scrollbar-thumb:hover { background: #c84b2f; }

/* ── Hide default Streamlit UI chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Download buttons ── */
.stDownloadButton button {
    background: transparent !important;
    color: #1a1a1a !important;
    border: 1.5px solid #1a1a1a !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border-radius: 0 !important;
}
.stDownloadButton button:hover {
    background: #1a1a1a !important;
    color: #f5f2ec !important;
}

/* ── Toggle ── */
.stToggle label { font-family: 'DM Mono', monospace !important; font-size: 0.78rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 1.5rem 0 1rem;'>
        <div style='font-family: Syne; font-weight: 800; font-size: 1.5rem;
             letter-spacing: -1px; color: #f5f2ec;'>
            Scrapi<span style='color:#c84b2f;'>py</span>
        </div>
        <div style='font-family: DM Mono; font-size: 0.6rem; letter-spacing: 3px;
             color: #555; text-transform: uppercase; margin-top: 4px;'>
            Configuration
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown('<div style="font-family:DM Mono;font-size:0.65rem;letter-spacing:2.5px;'
                'text-transform:uppercase;color:#555;margin-bottom:0.8rem;">Scraper</div>',
                unsafe_allow_html=True)

    force_selenium = st.toggle("Force Selenium (JS sites)", value=False)
    wait_time = st.slider("JS render wait (s)", 1, 10, 3)
    aggressive_clean = st.toggle("Aggressive cleaning", value=True)
    chunk_size = st.select_slider(
        "Chunk size (chars)", options=[3000, 4000, 6000, 8000, 10000], value=6000
    )

    st.divider()

    st.markdown('<div style="font-family:DM Mono;font-size:0.65rem;letter-spacing:2.5px;'
                'text-transform:uppercase;color:#555;margin-bottom:0.8rem;">AI Engine</div>',
                unsafe_allow_html=True)

    gemini_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="Free key: https://aistudio.google.com/app/apikey",
    )
    if gemini_key:
        import os
        os.environ["GEMINI_API_KEY"] = gemini_key

    ai_enabled = bool(gemini_key or __import__("os").getenv("GEMINI_API_KEY"))
    if ai_enabled:
        st.success("AI ready")
    else:
        st.caption("Enter a Gemini API key to enable AI parsing.")

    st.divider()

    st.markdown('<div style="font-family:DM Mono;font-size:0.65rem;letter-spacing:2.5px;'
                'text-transform:uppercase;color:#555;margin-bottom:0.8rem;">Batch Mode</div>',
                unsafe_allow_html=True)

    batch_raw = st.text_area(
        "URLs, one per line",
        height=90,
        placeholder="https://example.com\nhttps://another.com",
        label_visibility="collapsed",
    )
    batch_delay = st.slider("Delay between requests (s)", 0.5, 5.0, 1.5)

    if st.button("Run Batch", use_container_width=True):
        urls = [u.strip() for u in batch_raw.strip().splitlines() if u.strip()]
        if urls:
            with st.spinner(f"Scraping {len(urls)} URLs..."):
                results = scrape_multiple_urls(urls, delay=batch_delay)
                st.session_state.batch_results = results
            st.success(f"{len(results)} URLs done")
        else:
            st.warning("Enter at least one URL")

    if "batch_results" in st.session_state:
        df = pd.DataFrame([{
            "url": r.get("url", ""),
            "method": r.get("method", ""),
            "error": r.get("error", ""),
            "preview": r.get("text", "")[:200],
        } for r in st.session_state.batch_results])
        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            file_name="batch.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 2.5rem 0 1rem;'>
    <div class='wordmark'>Scrapi<span>py</span></div>
    <div class='tagline'>Web Intelligence, Extracted</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div style="height:1px;background:#d4d0c8;margin-bottom:1.5rem;"></div>',
            unsafe_allow_html=True)

# ── URL Input ─────────────────────────────────────────────────────────────────
col_url, col_btn = st.columns([5, 1])
with col_url:
    url = st.text_input(
        "",
        placeholder="Enter a URL  —  https://example.com",
        label_visibility="collapsed",
        key="url_input",
    )
with col_btn:
    scrape_btn = st.button("Fetch", use_container_width=True)

# ── Execute Scrape ────────────────────────────────────────────────────────────
if scrape_btn:
    if not url:
        st.warning("Please enter a URL.")
    else:
        bar = st.progress(0, text="Connecting...")
        try:
            bar.progress(15, text="Fetching page...")
            result = scrape_website(url, use_selenium=force_selenium, wait_time=wait_time)

            bar.progress(55, text="Extracting content...")
            html = result["html"]
            if not html:
                raise ValueError("No HTML returned. The site may be blocking scrapers.")

            body      = extract_body_content(html)
            cleaned   = clean_body_content(body, aggressive=aggressive_clean)
            article   = extract_article_content(html)
            metadata  = extract_metadata(html, url)
            structured = extract_structured_data(html)

            bar.progress(90, text="Finalizing...")
            time.sleep(0.2)

            st.session_state.update({
                "html": html,
                "body": body,
                "cleaned": cleaned,
                "article": article,
                "metadata": metadata,
                "structured": structured,
                "chunks": split_dom_content(cleaned, chunk_size),
                "result": result,
                "scraped_url": url,
            })
            bar.progress(100)
            time.sleep(0.3)
            bar.empty()

        except Exception as exc:
            bar.empty()
            st.error(f"Scrape failed: {exc}")
            st.stop()

# ── Results ───────────────────────────────────────────────────────────────────
if "result" in st.session_state:
    r        = st.session_state.result
    meta     = st.session_state.metadata
    chunks   = st.session_state.chunks
    struct   = st.session_state.structured

    # Stat bar
    st.markdown(f"""
    <div class='stat-row'>
        <div class='stat-card'>
            <div class='stat-label'>Method</div>
            <div class='stat-value' style='font-size:0.9rem;letter-spacing:1px;'>
                {r.get("method","—").upper()}
            </div>
        </div>
        <div class='stat-card'>
            <div class='stat-label'>Load Time</div>
            <div class='stat-value'>{r.get("elapsed","—")}s</div>
        </div>
        <div class='stat-card'>
            <div class='stat-label'>Words</div>
            <div class='stat-value'>{meta.get("word_count",0):,}</div>
        </div>
        <div class='stat-card'>
            <div class='stat-label'>Links</div>
            <div class='stat-value'>{len(meta.get("links",[]))}</div>
        </div>
        <div class='stat-card'>
            <div class='stat-label'>Images</div>
            <div class='stat-value'>{len(meta.get("images",[]))}</div>
        </div>
        <div class='stat-card'>
            <div class='stat-label'>Chunks</div>
            <div class='stat-value'>{len(chunks)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Page info
    if meta.get("title"):
        st.markdown(f"""
        <div class='page-card'>
            <div class='page-card-title'>{meta["title"]}</div>
            {'<div class="page-card-desc">' + meta["description"] + '</div>' if meta.get("description") else ""}
            <div style='margin-top:8px;'>
                <span class='method-badge'>{r.get("method","").upper()}</span>
                <span style='font-family:DM Mono;font-size:0.68rem;color:#888;margin-left:10px;'>
                    {r.get("timestamp","")[:19].replace("T","  ")}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Tabs
    tab_content, tab_meta, tab_ai, tab_export = st.tabs([
        "Content", "Metadata", "AI Analysis", "Export"
    ])

    # ── Content tab ──────────────────────────────────────────────────────────
    with tab_content:
        view = st.radio(
            "",
            ["Article Extract", "Cleaned Text", "Raw HTML"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if view == "Article Extract":
            st.markdown('<div class="sec-label">Smart Article Extraction</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="result-block">{st.session_state.article[:10000]}</div>',
                unsafe_allow_html=True
            )

        elif view == "Cleaned Text":
            st.markdown('<div class="sec-label">Cleaned Text Content</div>', unsafe_allow_html=True)
            with st.expander(f"View text  ({len(chunks)} chunk(s))", expanded=True):
                st.text_area("", st.session_state.cleaned[:12000], height=340,
                             label_visibility="collapsed")

        else:
            st.markdown('<div class="sec-label">Raw HTML Source</div>', unsafe_allow_html=True)
            with st.expander("View HTML"):
                st.code(st.session_state.html[:20000], language="html")

        headings = meta.get("headings", {})
        if headings:
            st.markdown('<div class="sec-label">Page Structure</div>', unsafe_allow_html=True)
            colors = {"h1": "#c84b2f", "h2": "#1a1a1a", "h3": "#555",
                      "h4": "#777", "h5": "#999", "h6": "#aaa"}
            for lvl, items in headings.items():
                indent = (int(lvl[1:]) - 1) * 18
                for item in items[:10]:
                    st.markdown(
                        f'<div class="heading-row" style="padding-left:{indent}px;">'
                        f'<span class="lvl" style="color:{colors.get(lvl,"#888")}">{lvl}</span>'
                        f'{item}</div>',
                        unsafe_allow_html=True,
                    )

    # ── Metadata tab ─────────────────────────────────────────────────────────
    with tab_meta:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="sec-label">SEO & Page Info</div>', unsafe_allow_html=True)
            seo = {
                "Title": meta.get("title", ""),
                "Description": meta.get("description", ""),
                "Keywords": meta.get("keywords", ""),
                "Language": meta.get("language", ""),
                "Canonical": meta.get("canonical", ""),
            }
            for k, v in seo.items():
                if v:
                    st.markdown(
                        f'<div style="margin-bottom:0.8rem;">'
                        f'<div style="font-family:DM Mono;font-size:0.65rem;letter-spacing:2px;'
                        f'text-transform:uppercase;color:#888;">{k}</div>'
                        f'<div style="font-size:0.88rem;color:#1a1a1a;margin-top:2px;">{v[:220]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            og = meta.get("og", {})
            if og:
                st.markdown('<div class="sec-label">Open Graph</div>', unsafe_allow_html=True)
                for k, v in og.items():
                    st.markdown(
                        f'<div style="font-family:DM Mono;font-size:0.75rem;margin:3px 0;">'
                        f'<span style="color:#c84b2f;">og:{k}</span>'
                        f'<span style="color:#666;margin-left:8px;">{str(v)[:100]}</span></div>',
                        unsafe_allow_html=True,
                    )

        with col2:
            st.markdown('<div class="sec-label">Contacts & Socials</div>', unsafe_allow_html=True)

            emails = meta.get("emails", [])
            if emails:
                st.markdown(
                    '<div style="font-family:DM Mono;font-size:0.65rem;letter-spacing:2px;'
                    'text-transform:uppercase;color:#888;margin-bottom:4px;">Emails</div>',
                    unsafe_allow_html=True,
                )
                for e in emails[:8]:
                    st.markdown(
                        f'<div style="font-family:DM Mono;font-size:0.8rem;padding:2px 0;'
                        f'color:#1a1a1a;">{e}</div>', unsafe_allow_html=True
                    )

            phones = meta.get("phone_numbers", [])
            if phones:
                st.markdown(
                    '<div style="font-family:DM Mono;font-size:0.65rem;letter-spacing:2px;'
                    'text-transform:uppercase;color:#888;margin:0.8rem 0 4px;">Phones</div>',
                    unsafe_allow_html=True,
                )
                for p in phones[:5]:
                    st.markdown(
                        f'<div style="font-family:DM Mono;font-size:0.8rem;color:#1a1a1a;">{p}</div>',
                        unsafe_allow_html=True,
                    )

            socials = list(set(meta.get("social_links", [])))
            if socials:
                st.markdown(
                    '<div style="font-family:DM Mono;font-size:0.65rem;letter-spacing:2px;'
                    'text-transform:uppercase;color:#888;margin:0.8rem 0 4px;">Social Links</div>',
                    unsafe_allow_html=True,
                )
                for s in socials[:8]:
                    st.markdown(
                        f'<a href="{s}" target="_blank" style="display:block;font-family:DM Mono;'
                        f'font-size:0.75rem;color:#c84b2f;text-decoration:none;margin:3px 0;'
                        f'word-break:break-all;">{s[:70]}</a>',
                        unsafe_allow_html=True,
                    )

        images = meta.get("images", [])
        if images:
            st.markdown('<div class="sec-label">Images Found</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(images[:50]), use_container_width=True, hide_index=True)

        tables = struct.get("tables", [])
        if tables:
            st.markdown('<div class="sec-label">Embedded Tables</div>', unsafe_allow_html=True)
            for i, tbl in enumerate(tables[:3]):
                with st.expander(f"Table {i+1}  —  {len(tbl)} rows"):
                    try:
                        st.dataframe(pd.DataFrame(tbl), use_container_width=True)
                    except Exception:
                        st.json(tbl)

        json_ld = struct.get("json_ld", [])
        if json_ld:
            st.markdown('<div class="sec-label">JSON-LD Structured Data</div>', unsafe_allow_html=True)
            with st.expander("View JSON-LD"):
                st.json(json_ld)

    # ── AI tab ───────────────────────────────────────────────────────────────
    with tab_ai:
        if not ai_enabled:
            st.info("Enter your Gemini API key in the sidebar to enable AI analysis. "
                    "Get a free key at https://aistudio.google.com/app/apikey")
        else:
            st.markdown('<div class="sec-label">AI Extraction  —  Gemini 1.5 Flash</div>',
                        unsafe_allow_html=True)

            col_p1, col_p2 = st.columns([3, 2])
            with col_p1:
                preset = st.selectbox("Preset tasks", [
                    "Custom query",
                    "Extract all prices and product names",
                    "Extract all article headlines",
                    "Extract contact information",
                    "List all links with anchor text",
                    "Extract company name, address, and hours",
                    "Extract all dates and events",
                    "Extract review scores and ratings",
                    "Extract job titles and company names",
                    "Pull all phone numbers and emails",
                ])
            with col_p2:
                mode = st.radio("Mode", ["Extract", "Summarize"], horizontal=True)

            if preset == "Custom query" or mode == "Summarize":
                task = st.text_area(
                    "Describe your extraction task" if mode == "Extract"
                    else "Optional notes for the summary",
                    height=70,
                    placeholder="e.g. Extract all product names with prices and availability...",
                )
            else:
                task = preset
                st.markdown(
                    f'<div style="font-family:DM Mono;font-size:0.78rem;color:#888;'
                    f'padding:0.5rem 0;">Task: {preset}</div>',
                    unsafe_allow_html=True,
                )

            col_run, col_clr = st.columns([4, 1])
            with col_run:
                run_btn = st.button("Run Analysis", use_container_width=True)
            with col_clr:
                if st.button("Clear", use_container_width=True):
                    st.session_state.pop("ai_result", None)
                    st.rerun()

            if run_btn:
                if mode == "Summarize":
                    with st.spinner("Generating summary..."):
                        try:
                            st.session_state.ai_result = summarize_with_gemini(chunks)
                        except Exception as exc:
                            st.error(str(exc))
                else:
                    if not task:
                        st.warning("Describe what to extract or select a preset.")
                    else:
                        bar2 = st.progress(0, text="Starting analysis...")
                        try:
                            # Process and update bar incrementally
                            from parse import _model, EXTRACT_PROMPT
                            model = _model()
                            results = []
                            for i, chunk in enumerate(chunks, 1):
                                bar2.progress(int(i / len(chunks) * 100),
                                              text=f"Chunk {i} of {len(chunks)}")
                                prompt = EXTRACT_PROMPT.format(content=chunk, task=task)
                                resp = model.generate_content(prompt)
                                text = resp.text.strip()
                                if text and text != "NO_MATCH":
                                    results.append(text)
                            bar2.empty()
                            st.session_state.ai_result = (
                                "\n\n".join(results) if results else "No matching content found."
                            )
                        except Exception as exc:
                            bar2.empty()
                            st.error(str(exc))

            if "ai_result" in st.session_state:
                st.markdown('<div class="sec-label">Result</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="result-block">{st.session_state.ai_result}</div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    "Download Result",
                    st.session_state.ai_result,
                    file_name=f"scrapipy_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                )

    # ── Export tab ───────────────────────────────────────────────────────────
    with tab_export:
        st.markdown('<div class="sec-label">Export Scraped Data</div>', unsafe_allow_html=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                "Cleaned Text  (.txt)",
                st.session_state.cleaned,
                file_name=f"scrapipy_text_{ts}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with c2:
            export_json = json.dumps({
                "url": st.session_state.scraped_url,
                "scraped_at": r.get("timestamp"),
                "method": r.get("method"),
                "metadata": meta,
                "structured_data": struct,
            }, indent=2, ensure_ascii=False)
            st.download_button(
                "Metadata  (.json)",
                export_json,
                file_name=f"scrapipy_meta_{ts}.json",
                mime="application/json",
                use_container_width=True,
            )
        with c3:
            if meta.get("links"):
                df_links = pd.DataFrame(meta["links"])
                st.download_button(
                    "All Links  (.csv)",
                    df_links.to_csv(index=False),
                    file_name=f"scrapipy_links_{ts}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        st.markdown('<div class="sec-label">Raw Exports</div>', unsafe_allow_html=True)
        c4, c5 = st.columns(2)
        with c4:
            st.download_button(
                "Full HTML Source",
                st.session_state.html,
                file_name=f"scrapipy_page_{ts}.html",
                mime="text/html",
                use_container_width=True,
            )
        with c5:
            st.download_button(
                "Article Extract  (.txt)",
                st.session_state.article,
                file_name=f"scrapipy_article_{ts}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        if meta.get("images"):
            st.markdown('<div class="sec-label">Images List</div>', unsafe_allow_html=True)
            st.download_button(
                "Images  (.csv)",
                pd.DataFrame(meta["images"]).to_csv(index=False),
                file_name=f"scrapipy_images_{ts}.csv",
                mime="text/csv",
            )
