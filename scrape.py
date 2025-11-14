import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.common.exceptions import WebDriverException, TimeoutException
from dotenv import load_dotenv

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env variables
load_dotenv()


# ---------------------------------------------------------------------------
# 🔐 AUTH HANDLING
# ---------------------------------------------------------------------------

def get_auth_credentials():
    """Validate and return Bright Data AUTH credentials."""
    auth = os.getenv("AUTH")

    if not auth:
        raise ValueError("AUTH not found. Add AUTH=username:password to .env")

    # Should contain ":" → username:password
    if ":" not in auth:
        raise ValueError(f"Invalid AUTH format: {auth}. Expected username:password")

    return auth


# ---------------------------------------------------------------------------
# 🧩 SELENIUM BROWSER SETUP
# ---------------------------------------------------------------------------

def get_chrome_options():
    """Configure Chrome for headless cloud environments."""
    options = ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return options


# ---------------------------------------------------------------------------
# 🚀 MAIN SCRAPER (Bright Data Scraping Browser)
# ---------------------------------------------------------------------------

def scrape_website(website, max_retries=3, timeout=30):
    """
    Scrape a webpage using Bright Data's Scraping Browser.
    Includes captcha support, retries, exponential backoff.
    """
    auth = get_auth_credentials()
    sbr_url = f"https://{auth}@brd.superproxy.io:9515"

    logger.info(f"Connecting to Bright Data Browser → {website}")

    for attempt in range(1, max_retries + 1):
        driver = None
        logger.info(f"Attempt {attempt}/{max_retries}")

        try:
            # Create new remote Chrome instance
            connection = ChromiumRemoteConnection(sbr_url, "goog", "chrome")
            options = get_chrome_options()
            driver = Remote(connection, options=options)

            driver.set_page_load_timeout(timeout)
            driver.implicitly_wait(10)

            # Navigate to site
            driver.get(website)
            logger.info("Page loaded successfully!")

            # Try solving captchas automatically
            try:
                solve_res = driver.execute(
                    "executeCdpCommand",
                    {
                        "cmd": "Captcha.waitForSolve",
                        "params": {"detectTimeout": 10000},
                    }
                )
                logger.info(f"Captcha status: {solve_res['value']['status']}")
            except Exception:
                logger.info("No captcha detected (or unsupported).")

            html = driver.page_source

            if html and len(html) > 200:
                logger.info(f"Scraped {len(html)} characters successfully.")
                return html

            raise Exception("Received empty/short HTML content.")

        except WebDriverException as e:
            logger.error(f"Selenium error: {e}")

            if "Wrong customer name" in str(e):
                raise ValueError(
                    "❌ Bright Data AUTH is incorrect.\n"
                    "Fix AUTH=username:password in your .env file."
                )

            if attempt < max_retries:
                time.sleep(2 ** attempt)
            else:
                raise Exception(f"Failed after {max_retries} attempts → {e}")

        except TimeoutException as e:
            logger.error(f"Timeout: {e}")
            if attempt == max_retries:
                raise Exception("Page load timed out repeatedly")
            time.sleep(2)

        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass


# ---------------------------------------------------------------------------
# 🧽 CLEANERS
# ---------------------------------------------------------------------------

def extract_body_content(html_content):
    """Extract <body>...</body> from HTML."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        return str(soup.body) if soup.body else ""
    except Exception as e:
        logger.error(f"extract_body_content error: {e}")
        return ""


def clean_body_content(body_content):
    """Clean text by removing scripts, styles, and extra whitespace."""
    try:
        soup = BeautifulSoup(body_content, "html.parser")

        # Remove scripts & styles
        for bad in soup(["script", "style"]):
            bad.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    except Exception as e:
        logger.error(f"clean_body_content error: {e}")
        return ""


def split_dom_content(dom_content, max_length=6000):
    """Split large text into LLM-friendly chunks."""
    return [
        dom_content[i:i + max_length]
        for i in range(0, len(dom_content), max_length)
    ] if dom_content else []


# ---------------------------------------------------------------------------
# 🛟 FALLBACK SCRAPER (Requests)
# ---------------------------------------------------------------------------

def fallback_scrape(website):
    """Fallback scraper using requests (no JS support)."""
    try:
        logger.info("Fallback scraper (requests) activated.")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        res = requests.get(website, headers=headers, timeout=12)
        res.raise_for_status()
        return res.text

    except Exception as e:
        logger.error(f"Fallback failed: {e}")
        raise Exception("Fallback scraping failed as well.")


# ---------------------------------------------------------------------------
# 🔄 AUTO-FAILOVER LOGIC
# ---------------------------------------------------------------------------

def scrape_with_fallback(website):
    """Try Bright Data first, fallback to requests if something fails."""
    try:
        return scrape_website(website)
    except Exception as e:
        logger.warning(f"Main scraper failed → {e}")
        logger.info("Attempting fallback requests scraper...")
        return fallback_scrape(website)
