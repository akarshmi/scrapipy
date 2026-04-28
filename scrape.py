import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
from urllib.parse import urljoin, urlparse
from datetime import datetime

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }

def scrape_website(url, use_selenium=False, wait_time=3):
    """
    Primary scraper. Tries requests first, falls back to Selenium.
    Returns dict with html, status, method, timing, metadata.
    """
    start = time.time()
    result = {
        "url": url,
        "html": "",
        "status_code": None,
        "method": None,
        "elapsed": 0,
        "timestamp": datetime.now().isoformat(),
        "error": None,
        "metadata": {}
    }

    if use_selenium:
        result["html"] = _scrape_with_selenium(url, wait_time)
        result["method"] = "selenium"
        result["elapsed"] = round(time.time() - start, 2)
        return result

    try:
        session = requests.Session()
        # Warm session with a HEAD request first
        try:
            session.head(url, headers=get_headers(), timeout=5, allow_redirects=True)
            time.sleep(0.5)
        except:
            pass

        response = session.get(
            url,
            headers=get_headers(),
            timeout=20,
            allow_redirects=True,
        )
        result["status_code"] = response.status_code
        response.raise_for_status()
        html = response.text

        # Detect JS-heavy page
        soup = BeautifulSoup(html, "html.parser")
        visible_text = soup.get_text(strip=True)

        if len(visible_text) < 300 or _is_js_heavy(html):
            print("⚠️  JS-heavy page detected — switching to Selenium")
            result["html"] = _scrape_with_selenium(url, wait_time)
            result["method"] = "selenium"
        else:
            result["html"] = html
            result["method"] = "requests"

    except requests.exceptions.HTTPError as e:
        result["error"] = f"HTTP {e.response.status_code}"
        result["html"] = _scrape_with_selenium(url, wait_time)
        result["method"] = "selenium (fallback)"
    except Exception as e:
        result["error"] = str(e)
        result["html"] = _scrape_with_selenium(url, wait_time)
        result["method"] = "selenium (fallback)"

    result["elapsed"] = round(time.time() - start, 2)
    return result


def _is_js_heavy(html):
    """Detect React/Vue/Angular/Next.js single-page apps."""
    patterns = [
        r'<div id=["\']root["\']>\s*</div>',
        r'<div id=["\']app["\']>\s*</div>',
        r'__NEXT_DATA__',
        r'window\.__nuxt__',
        r'ng-version=',
        r'data-reactroot',
    ]
    return any(re.search(p, html) for p in patterns)


def _scrape_with_selenium(url, wait_time=3):
    """Headless Chrome scraper for JS-rendered pages."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
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
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            driver.get(url)
            # Wait for body to have content
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_element(By.TAG_NAME, "body").text) > 100
            )
            time.sleep(wait_time)

            # Scroll to load lazy content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            return driver.page_source
        finally:
            driver.quit()

    except ImportError:
        raise RuntimeError("Selenium not installed. Run: pip install selenium")
    except Exception as e:
        raise RuntimeError(f"Selenium failed: {e}")


# ─── Content Extraction ───────────────────────────────────────────────────────

def extract_body_content(html):
    soup = BeautifulSoup(html, "html.parser")
    body = soup.body
    return str(body) if body else str(soup)


def extract_metadata(html, url=""):
    """Extract all page metadata: title, description, OG tags, schema, links."""
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

    # Title
    title_tag = soup.find("title")
    meta["title"] = title_tag.get_text(strip=True) if title_tag else ""

    # Meta tags
    for tag in soup.find_all("meta"):
        name = tag.get("name", "").lower()
        prop = tag.get("property", "").lower()
        content = tag.get("content", "")

        if name == "description":
            meta["description"] = content
        elif name == "keywords":
            meta["keywords"] = content
        elif name == "language" or tag.get("http-equiv", "").lower() == "content-language":
            meta["language"] = content
        elif prop.startswith("og:"):
            meta["og"][prop[3:]] = content
        elif prop.startswith("twitter:") or name.startswith("twitter:"):
            key = prop[8:] or name[8:]
            meta["twitter"][key] = content

    # Canonical
    canonical = soup.find("link", rel="canonical")
    if canonical:
        meta["canonical"] = canonical.get("href", "")

    # Language from html tag
    html_tag = soup.find("html")
    if html_tag and not meta["language"]:
        meta["language"] = html_tag.get("lang", "")

    # All links
    base = urlparse(url)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(url, href)
        text = a.get_text(strip=True)
        meta["links"].append({"text": text, "href": full})

        # Social links
        social_domains = ["twitter.com", "x.com", "facebook.com", "instagram.com",
                          "linkedin.com", "youtube.com", "github.com", "tiktok.com"]
        if any(s in full for s in social_domains):
            meta["social_links"].append(full)

    # Images
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src:
            meta["images"].append({
                "src": urljoin(url, src),
                "alt": img.get("alt", ""),
                "title": img.get("title", ""),
            })

    # Emails and phones from text
    text_content = soup.get_text()
    meta["emails"] = list(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text_content)))
    meta["phone_numbers"] = list(set(re.findall(
        r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{3,4}", text_content
    )))

    # Headings structure
    for level in range(1, 7):
        tags = soup.find_all(f"h{level}")
        if tags:
            meta["headings"][f"h{level}"] = [t.get_text(strip=True) for t in tags]

    # Word count
    meta["word_count"] = len(text_content.split())

    return meta


def extract_structured_data(html):
    """Extract JSON-LD, microdata, and tables."""
    soup = BeautifulSoup(html, "html.parser")
    data = {"json_ld": [], "tables": []}

    # JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data["json_ld"].append(json.loads(script.string))
        except:
            pass

    # Tables → list of dicts
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


def clean_body_content(body_content, aggressive=False):
    """
    Clean HTML to plain text.
    aggressive=True: strip nav/footer/ads for article extraction.
    """
    soup = BeautifulSoup(body_content, "html.parser")

    remove_tags = ["script", "style", "noscript", "iframe", "embed", "object"]
    if aggressive:
        remove_tags += ["nav", "footer", "header", "aside", "form",
                        "button", "input", "select", "textarea"]

    for tag in soup(remove_tags):
        tag.decompose()

    # Remove hidden elements
    for tag in soup.find_all(style=re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden")):
        tag.decompose()

    # Preserve structure with newlines
    for tag in soup.find_all(["h1","h2","h3","h4","h5","h6"]):
        tag.insert_before("\n\n### ")
        tag.insert_after("\n")

    for tag in soup.find_all(["p", "li", "br", "div", "tr"]):
        tag.insert_after("\n")

    text = soup.get_text(separator=" ")

    # Normalize whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)

    # Remove repeated blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def extract_article_content(html):
    """
    Smart article extraction — finds the main content block
    by scoring elements on text density, link density, and tag signals.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise
    for tag in soup(["script","style","nav","footer","header","aside","form","advertisement"]):
        tag.decompose()

    # Score candidate blocks
    candidates = []
    for tag in soup.find_all(["article","main","div","section"]):
        text = tag.get_text(strip=True)
        if len(text) < 100:
            continue
        links = tag.find_all("a")
        link_text = " ".join(a.get_text(strip=True) for a in links)
        link_density = len(link_text) / max(len(text), 1)
        score = len(text) * (1 - link_density)

        # Boost known content tags
        if tag.name in ["article", "main"]:
            score *= 2
        if tag.get("id") in ["content","main","article","post","entry"]:
            score *= 1.5
        if any(c in tag.get("class", []) for c in ["content","article","post","entry","body"]):
            score *= 1.3

        candidates.append((score, tag))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1].get_text(separator="\n", strip=True)

    return soup.get_text(separator="\n", strip=True)


def split_dom_content(dom_content, max_length=6000):
    """Split content into chunks, trying to preserve paragraph boundaries."""
    if len(dom_content) <= max_length:
        return [dom_content]

    chunks = []
    paragraphs = dom_content.split("\n\n")
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_length:
            current += ("\n\n" if current else "") + para
        else:
            if current:
                chunks.append(current)
            # If single paragraph is too long, hard-split it
            while len(para) > max_length:
                chunks.append(para[:max_length])
                para = para[max_length:]
            current = para

    if current:
        chunks.append(current)

    return chunks


def scrape_multiple_urls(urls, delay=1.5):
    """Scrape a list of URLs with polite delay between requests."""
    results = []
    for i, url in enumerate(urls):
        print(f"Scraping {i+1}/{len(urls)}: {url}")
        try:
            result = scrape_website(url)
            result["body"] = extract_body_content(result["html"])
            result["text"] = clean_body_content(result["body"], aggressive=True)
            results.append(result)
        except Exception as e:
            results.append({"url": url, "error": str(e), "html": ""})
        if i < len(urls) - 1:
            time.sleep(delay + random.uniform(0, 1))
    return results
