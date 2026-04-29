import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
from urllib.parse import urljoin, urlparse
from datetime import datetime

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]

def _headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }


def _is_js_heavy(html):
    signals = [
        r'<div id=["\']root["\']>\s*</div>',
        r'<div id=["\']app["\']>\s*</div>',
        r'__NEXT_DATA__',
        r'window\.__nuxt__',
        r'ng-version=',
        r'data-reactroot',
    ]
    return any(re.search(p, html) for p in signals)


def _scrape_with_selenium(url, wait_time=3):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.common.by import By

        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=opts)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        try:
            driver.get(url)
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: len(d.find_element(By.TAG_NAME, "body").text) > 100
                )
            except Exception:
                pass
            time.sleep(wait_time)
            # Scroll to trigger lazy-loads
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(0.8)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.8)
            return driver.page_source
        finally:
            driver.quit()
    except ImportError:
        raise RuntimeError(
            "Selenium is not installed. Run: pip install selenium  "
            "and install ChromeDriver matching your Chrome version."
        )
    except Exception as exc:
        raise RuntimeError(f"Selenium failed: {exc}")


def scrape_website(url, use_selenium=False, wait_time=3):
    start = time.time()
    record = {
        "url": url,
        "html": "",
        "status_code": None,
        "method": None,
        "elapsed": 0,
        "timestamp": datetime.now().isoformat(),
        "error": None,
    }

    if use_selenium:
        record["html"] = _scrape_with_selenium(url, wait_time)
        record["method"] = "selenium"
        record["elapsed"] = round(time.time() - start, 2)
        return record

    try:
        session = requests.Session()
        # Warm the session
        try:
            session.head(url, headers=_headers(), timeout=6, allow_redirects=True)
            time.sleep(random.uniform(0.3, 0.8))
        except Exception:
            pass

        resp = session.get(url, headers=_headers(), timeout=25, allow_redirects=True)
        record["status_code"] = resp.status_code
        resp.raise_for_status()
        html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        visible = soup.get_text(strip=True)

        if len(visible) < 300 or _is_js_heavy(html):
            record["html"] = _scrape_with_selenium(url, wait_time)
            record["method"] = "selenium (JS page)"
        else:
            record["html"] = html
            record["method"] = "requests"

    except requests.exceptions.HTTPError as exc:
        record["error"] = f"HTTP {exc.response.status_code}"
        record["html"] = _scrape_with_selenium(url, wait_time)
        record["method"] = "selenium (fallback)"
    except Exception as exc:
        record["error"] = str(exc)
        record["html"] = _scrape_with_selenium(url, wait_time)
        record["method"] = "selenium (fallback)"

    record["elapsed"] = round(time.time() - start, 2)
    return record


# ---------- Extraction helpers ----------

def extract_body_content(html):
    soup = BeautifulSoup(html, "html.parser")
    body = soup.body
    return str(body) if body else str(soup)


def extract_metadata(html, url=""):
    soup = BeautifulSoup(html, "html.parser")
    meta = {
        "title": "",
        "description": "",
        "keywords": "",
        "og": {},
        "twitter": {},
        "canonical": "",
        "language": "",
        "links": [],
        "images": [],
        "emails": [],
        "phone_numbers": [],
        "social_links": [],
        "word_count": 0,
        "headings": {},
    }

    title_tag = soup.find("title")
    meta["title"] = title_tag.get_text(strip=True) if title_tag else ""

    for tag in soup.find_all("meta"):
        name = tag.get("name", "").lower()
        prop = tag.get("property", "").lower()
        content = tag.get("content", "")
        if name == "description":
            meta["description"] = content
        elif name == "keywords":
            meta["keywords"] = content
        elif prop.startswith("og:"):
            meta["og"][prop[3:]] = content
        elif prop.startswith("twitter:") or name.startswith("twitter:"):
            meta["twitter"][prop[8:] or name[8:]] = content

    canonical = soup.find("link", rel="canonical")
    if canonical:
        meta["canonical"] = canonical.get("href", "")

    html_tag = soup.find("html")
    if html_tag:
        meta["language"] = html_tag.get("lang", "")

    social_domains = [
        "twitter.com", "x.com", "facebook.com", "instagram.com",
        "linkedin.com", "youtube.com", "github.com", "tiktok.com",
    ]
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"])
        meta["links"].append({"text": a.get_text(strip=True), "href": href})
        if any(s in href for s in social_domains):
            meta["social_links"].append(href)

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src:
            meta["images"].append({
                "src": urljoin(url, src),
                "alt": img.get("alt", ""),
            })

    text_all = soup.get_text()
    meta["emails"] = list(set(re.findall(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text_all
    )))
    meta["phone_numbers"] = list(set(re.findall(
        r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{3,4}",
        text_all,
    )))

    for lvl in range(1, 7):
        tags = soup.find_all(f"h{lvl}")
        if tags:
            meta["headings"][f"h{lvl}"] = [t.get_text(strip=True) for t in tags]

    meta["word_count"] = len(text_all.split())
    return meta


def extract_structured_data(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {"json_ld": [], "tables": []}

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data["json_ld"].append(json.loads(script.string))
        except Exception:
            pass

    for table in soup.find_all("table"):
        rows = []
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells:
                if headers and len(cells) == len(headers):
                    rows.append(dict(zip(headers, cells)))
                else:
                    rows.append(cells)
        if rows:
            data["tables"].append(rows)

    return data


def extract_article_content(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    candidates = []
    for tag in soup.find_all(["article", "main", "div", "section"]):
        text = tag.get_text(strip=True)
        if len(text) < 150:
            continue
        links = tag.find_all("a")
        link_text = " ".join(a.get_text(strip=True) for a in links)
        link_density = len(link_text) / max(len(text), 1)
        score = len(text) * (1 - link_density)
        if tag.name in ["article", "main"]:
            score *= 2
        if tag.get("id") in ["content", "main", "article", "post", "entry"]:
            score *= 1.5
        if any(c in tag.get("class", []) for c in ["content", "article", "post", "entry"]):
            score *= 1.3
        candidates.append((score, tag))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1].get_text(separator="\n", strip=True)
    return soup.get_text(separator="\n", strip=True)


def clean_body_content(body_content, aggressive=False):
    soup = BeautifulSoup(body_content, "html.parser")
    remove = ["script", "style", "noscript", "iframe", "embed", "object"]
    if aggressive:
        remove += ["nav", "footer", "header", "aside", "form",
                   "button", "input", "select", "textarea"]
    for tag in soup(remove):
        tag.decompose()
    for tag in soup.find_all(style=re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden")):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    text = "\n".join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def split_dom_content(dom_content, max_length=6000):
    if len(dom_content) <= max_length:
        return [dom_content]
    chunks, current = [], ""
    for para in dom_content.split("\n\n"):
        if len(current) + len(para) + 2 <= max_length:
            current += ("\n\n" if current else "") + para
        else:
            if current:
                chunks.append(current)
            while len(para) > max_length:
                chunks.append(para[:max_length])
                para = para[max_length:]
            current = para
    if current:
        chunks.append(current)
    return chunks


def scrape_multiple_urls(urls, delay=1.5):
    results = []
    for i, url in enumerate(urls):
        try:
            r = scrape_website(url)
            r["body"] = extract_body_content(r["html"])
            r["text"] = clean_body_content(r["body"], aggressive=True)
            results.append(r)
        except Exception as exc:
            results.append({"url": url, "error": str(exc), "html": ""})
        if i < len(urls) - 1:
            time.sleep(delay + random.uniform(0, 0.8))
    return results
