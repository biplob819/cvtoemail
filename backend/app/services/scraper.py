"""Web scraper for job listings -- httpx + BeautifulSoup4 with anti-blocking measures.

Features:
- User-Agent rotation (20+ real browser strings)
- Full browser-like headers (Accept, Accept-Language, Referer)
- Random delay between requests (2-10s)
- Per-domain rate limiter (max 1 request per minute)
- Session/cookie reuse
- Optional proxy support (configurable via PROXY_URL env var)
- Playwright fallback for JS-rendered pages
"""

import asyncio
import hashlib
import random
import time
from typing import Optional
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup

from app.config import settings


# ---------------------------------------------------------------------------
# User-Agent rotation pool (20+ real browser strings)
# ---------------------------------------------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
]


# ---------------------------------------------------------------------------
# Per-domain rate limiter (max 1 request per minute)
# ---------------------------------------------------------------------------

_domain_last_request: dict[str, float] = {}
_DOMAIN_RATE_LIMIT_SECONDS = 60


def _get_domain(url: str) -> str:
    """Extract the domain from a URL."""
    return urlparse(url).netloc


async def _wait_for_rate_limit(url: str) -> None:
    """Enforce per-domain rate limit: wait if the last request was too recent."""
    domain = _get_domain(url)
    now = time.monotonic()
    last = _domain_last_request.get(domain, 0)
    wait_time = _DOMAIN_RATE_LIMIT_SECONDS - (now - last)
    if wait_time > 0:
        await asyncio.sleep(wait_time)
    _domain_last_request[domain] = time.monotonic()


def _build_headers(url: str) -> dict[str, str]:
    """Build browser-like request headers with a random User-Agent."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": f"{urlparse(url).scheme}://{urlparse(url).netloc}/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


def _get_proxy() -> Optional[str]:
    """Return the configured proxy URL, if any."""
    proxy_url = getattr(settings, "proxy_url", None)
    if proxy_url and proxy_url.strip():
        return proxy_url.strip()
    return None


# ---------------------------------------------------------------------------
# HTML parsing -- extract job listings from a page
# ---------------------------------------------------------------------------

def parse_job_listings(html: str, base_url: str) -> list[dict]:
    """Extract job listings from HTML content.

    This is a generic parser that looks for common job listing patterns:
    - Links with job-related keywords in href or text
    - Structured data with title, company, location
    - Common HTML patterns used by career pages

    Returns a list of dicts with: title, company, location, url, description
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    # Strategy 1: Look for structured job listing containers
    # Common patterns: .job-listing, .job-card, .job-item, [data-job], etc.
    job_selectors = [
        "[class*='job-listing']",
        "[class*='job-card']",
        "[class*='job-item']",
        "[class*='job-post']",
        "[class*='job-result']",
        "[class*='vacancy']",
        "[class*='opening']",
        "[class*='position']",
        "[data-job-id]",
        "[data-entity-urn]",
        "article[class*='job']",
        ".posting-card",
        ".careers-listing",
    ]

    for selector in job_selectors:
        elements = soup.select(selector)
        for el in elements:
            job = _extract_job_from_element(el, base_url)
            if job and job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                jobs.append(job)

    # Strategy 2: Look for links that are likely job postings
    if not jobs:
        job_link_patterns = [
            "/job/", "/jobs/", "/position/", "/positions/",
            "/career/", "/careers/", "/vacancy/", "/vacancies/",
            "/opening/", "/openings/", "/posting/", "/apply/",
        ]
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            href_lower = href.lower()
            if any(pattern in href_lower for pattern in job_link_patterns):
                full_url = urljoin(base_url, href)
                if full_url not in seen_urls:
                    title = link.get_text(strip=True) or "Untitled Position"
                    if len(title) > 5:  # Filter out very short/empty link texts
                        seen_urls.add(full_url)
                        jobs.append({
                            "title": title[:200],
                            "company": "",
                            "location": "",
                            "url": full_url,
                            "description": "",
                        })

    return jobs


def _extract_job_from_element(element, base_url: str) -> Optional[dict]:
    """Extract job details from a container element."""
    # Find the primary link (job URL)
    link = element.find("a", href=True)
    if not link:
        return None

    url = urljoin(base_url, link.get("href", ""))
    if not url or url == base_url:
        return None

    # Title: from the link text, or heading elements
    title = ""
    for tag in ["h1", "h2", "h3", "h4", "a"]:
        title_el = element.find(tag)
        if title_el:
            title = title_el.get_text(strip=True)
            if title:
                break
    if not title:
        title = link.get_text(strip=True) or "Untitled Position"

    # Company: look for common class patterns
    company = ""
    company_selectors = [
        "[class*='company']", "[class*='employer']",
        "[class*='organization']", "[data-company]",
    ]
    for sel in company_selectors:
        comp_el = element.select_one(sel)
        if comp_el:
            company = comp_el.get_text(strip=True)
            break

    # Location: look for common class patterns
    location = ""
    location_selectors = [
        "[class*='location']", "[class*='city']",
        "[class*='region']", "[data-location]",
    ]
    for sel in location_selectors:
        loc_el = element.select_one(sel)
        if loc_el:
            location = loc_el.get_text(strip=True)
            break

    return {
        "title": title[:200],
        "company": company[:200],
        "location": location[:200],
        "url": url,
        "description": "",
    }


# ---------------------------------------------------------------------------
# Playwright fallback for JS-rendered pages
# ---------------------------------------------------------------------------

async def _fetch_with_playwright(url: str) -> Optional[str]:
    """Fetch page HTML using Playwright (headless browser) for JS-rendered content."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent=random.choice(USER_AGENTS),
            )
            await page.goto(url, wait_until="networkidle", timeout=30000)
            html = await page.content()
            await browser.close()
            return html
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Main scraping function
# ---------------------------------------------------------------------------

async def scrape_source(url: str) -> list[dict]:
    """Scrape a URL for job listings.

    1. Enforces per-domain rate limiting
    2. Adds random delay (2-10s)
    3. Fetches with httpx + stealth headers + session/cookies
    4. Falls back to Playwright if httpx returns suspicious content
    5. Parses HTML for job listings

    Returns a list of dicts with: title, company, location, url, description
    """
    # Rate limit
    await _wait_for_rate_limit(url)

    # Random delay (2-10 seconds)
    delay = random.uniform(2.0, 10.0)
    await asyncio.sleep(delay)

    html: Optional[str] = None
    proxy = _get_proxy()

    # Attempt 1: httpx with stealth headers
    try:
        transport_kwargs = {}
        if proxy:
            transport_kwargs["proxy"] = proxy

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(30.0),
            headers=_build_headers(url),
            **transport_kwargs,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
    except Exception:
        html = None

    # Check if we got meaningful HTML
    if html and _looks_like_blocked(html):
        html = None  # Try Playwright

    # Attempt 2: Playwright fallback for JS-rendered pages or blocked requests
    if not html:
        html = await _fetch_with_playwright(url)

    if not html:
        raise RuntimeError(f"Failed to fetch content from {url}")

    # Parse job listings
    return parse_job_listings(html, url)


def _looks_like_blocked(html: str) -> bool:
    """Heuristic check if the response looks like a block/captcha page."""
    lower = html.lower()
    # Very short pages are suspicious
    if len(html) < 500:
        return True
    # Common blocking indicators
    block_signals = [
        "captcha", "robot", "blocked", "access denied",
        "please verify", "unusual traffic", "cloudflare",
    ]
    # If the page is short AND has blocking keywords
    if len(html) < 5000:
        return any(signal in lower for signal in block_signals)
    return False


def hash_job_url(url: str) -> str:
    """Create a consistent hash for deduplication."""
    return hashlib.sha256(url.encode()).hexdigest()
