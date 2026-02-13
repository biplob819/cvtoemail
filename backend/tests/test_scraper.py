"""Unit tests for the scraper service -- HTML parsing, stealth headers, rate limiting."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.scraper import (
    parse_job_listings,
    _build_headers,
    _get_domain,
    _looks_like_blocked,
    hash_job_url,
    USER_AGENTS,
    scrape_source,
)


# ---------------------------------------------------------------------------
# parse_job_listings tests
# ---------------------------------------------------------------------------

class TestParseJobListings:
    """Tests for the HTML parser that extracts job listings."""

    @pytest.mark.unit
    def test_parse_structured_job_cards(self):
        """Should extract jobs from elements with job-related class names."""
        html = """
        <html><body>
        <div class="job-listing">
            <h3><a href="/careers/123">Senior Developer</a></h3>
            <span class="company-name">TechCo</span>
            <span class="location">Remote</span>
        </div>
        <div class="job-listing">
            <h3><a href="/careers/456">Product Manager</a></h3>
            <span class="company-name">StartupInc</span>
            <span class="location">New York</span>
        </div>
        </body></html>
        """
        jobs = parse_job_listings(html, "https://example.com")
        assert len(jobs) == 2
        assert jobs[0]["title"] == "Senior Developer"
        assert jobs[0]["company"] == "TechCo"
        assert jobs[0]["location"] == "Remote"
        assert jobs[0]["url"] == "https://example.com/careers/123"
        assert jobs[1]["title"] == "Product Manager"

    @pytest.mark.unit
    def test_parse_job_links(self):
        """Should extract jobs from links with job-related URL patterns."""
        html = """
        <html><body>
        <ul>
            <li><a href="/jobs/senior-engineer">Senior Engineer at Google</a></li>
            <li><a href="/jobs/product-designer">Product Designer Role</a></li>
            <li><a href="/about">About Us</a></li>
        </ul>
        </body></html>
        """
        jobs = parse_job_listings(html, "https://example.com")
        assert len(jobs) == 2
        assert jobs[0]["title"] == "Senior Engineer at Google"
        assert jobs[0]["url"] == "https://example.com/jobs/senior-engineer"

    @pytest.mark.unit
    def test_parse_no_jobs(self):
        """Should return empty list when no job listings found."""
        html = """
        <html><body>
        <h1>Welcome to our company</h1>
        <p>We are a great place to work.</p>
        </body></html>
        """
        jobs = parse_job_listings(html, "https://example.com")
        assert jobs == []

    @pytest.mark.unit
    def test_parse_deduplicates_urls(self):
        """Should not return duplicate job URLs."""
        html = """
        <html><body>
        <div class="job-card"><a href="/jobs/123">Developer</a></div>
        <div class="job-card"><a href="/jobs/123">Developer (duplicate)</a></div>
        <div class="job-card"><a href="/jobs/456">Designer</a></div>
        </body></html>
        """
        jobs = parse_job_listings(html, "https://example.com")
        urls = [j["url"] for j in jobs]
        assert len(urls) == len(set(urls))  # No duplicates

    @pytest.mark.unit
    def test_parse_resolves_relative_urls(self):
        """Should resolve relative URLs against the base URL."""
        html = """
        <html><body>
        <div class="job-item">
            <a href="/careers/openings/789">Full Stack Developer</a>
        </div>
        </body></html>
        """
        jobs = parse_job_listings(html, "https://company.com")
        assert len(jobs) >= 1
        assert jobs[0]["url"].startswith("https://company.com/")

    @pytest.mark.unit
    def test_parse_vacancy_class(self):
        """Should find jobs in elements with 'vacancy' class."""
        html = """
        <html><body>
        <div class="vacancy">
            <a href="/apply/v1">Backend Engineer</a>
            <div class="company">Corp Ltd</div>
        </div>
        </body></html>
        """
        jobs = parse_job_listings(html, "https://example.com")
        assert len(jobs) >= 1
        assert "Backend Engineer" in jobs[0]["title"]

    @pytest.mark.unit
    def test_parse_truncates_long_titles(self):
        """Should truncate very long titles to 200 chars."""
        long_title = "A" * 300
        html = f"""
        <html><body>
        <div class="job-listing">
            <a href="/jobs/long">{long_title}</a>
        </div>
        </body></html>
        """
        jobs = parse_job_listings(html, "https://example.com")
        if jobs:
            assert len(jobs[0]["title"]) <= 200


# ---------------------------------------------------------------------------
# Stealth headers tests
# ---------------------------------------------------------------------------

class TestStealthHeaders:
    """Tests for anti-blocking stealth headers."""

    @pytest.mark.unit
    def test_user_agent_pool_size(self):
        """Should have at least 20 User-Agent strings."""
        assert len(USER_AGENTS) >= 20

    @pytest.mark.unit
    def test_user_agents_are_realistic(self):
        """User-Agent strings should look like real browsers."""
        for ua in USER_AGENTS:
            assert "Mozilla" in ua
            assert len(ua) > 50

    @pytest.mark.unit
    def test_build_headers_includes_required_fields(self):
        """Headers should include all browser-like fields."""
        headers = _build_headers("https://example.com")
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "Referer" in headers
        assert headers["Referer"] == "https://example.com/"

    @pytest.mark.unit
    def test_build_headers_user_agent_from_pool(self):
        """User-Agent in headers should come from the rotation pool."""
        headers = _build_headers("https://example.com")
        assert headers["User-Agent"] in USER_AGENTS


# ---------------------------------------------------------------------------
# Utility tests
# ---------------------------------------------------------------------------

class TestScraperUtilities:
    """Tests for scraper utility functions."""

    @pytest.mark.unit
    def test_get_domain(self):
        """Should correctly extract domain from URL."""
        assert _get_domain("https://example.com/path") == "example.com"
        assert _get_domain("http://sub.domain.co.uk/jobs") == "sub.domain.co.uk"

    @pytest.mark.unit
    def test_looks_like_blocked_short_page(self):
        """Very short pages should be flagged as potentially blocked."""
        assert _looks_like_blocked("<html><body>Please wait...</body></html>") is True

    @pytest.mark.unit
    def test_looks_like_blocked_captcha(self):
        """Pages with captcha keywords should be flagged."""
        html = "<html><body><p>Please complete the CAPTCHA to continue</p>" + "x" * 1000 + "</body></html>"
        assert _looks_like_blocked(html) is True

    @pytest.mark.unit
    def test_looks_like_blocked_normal_page(self):
        """Normal pages with enough content should not be flagged."""
        html = "<html><body>" + "<p>Normal content here.</p>" * 500 + "</body></html>"
        assert _looks_like_blocked(html) is False

    @pytest.mark.unit
    def test_hash_job_url_consistent(self):
        """Hash should be consistent for the same URL."""
        url = "https://example.com/jobs/123"
        assert hash_job_url(url) == hash_job_url(url)

    @pytest.mark.unit
    def test_hash_job_url_different(self):
        """Different URLs should produce different hashes."""
        assert hash_job_url("https://a.com/1") != hash_job_url("https://a.com/2")


# ---------------------------------------------------------------------------
# scrape_source integration tests (with mocked HTTP)
# ---------------------------------------------------------------------------

class TestScrapeSource:
    """Tests for the main scrape_source function with mocked HTTP."""

    @pytest.mark.unit
    async def test_scrape_source_success(self):
        """Should fetch and parse a page successfully."""
        # HTML must be >500 chars to pass the _looks_like_blocked heuristic
        padding = "<!-- padding -->" * 40
        mock_html = f"""
        <html><body>
        {padding}
        <div class="job-listing">
            <a href="/jobs/1">Frontend Developer</a>
            <span class="company-name">TestCo</span>
        </div>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.scraper._wait_for_rate_limit", new_callable=AsyncMock), \
             patch("app.services.scraper.asyncio.sleep", new_callable=AsyncMock), \
             patch("app.services.scraper.httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            jobs = await scrape_source("https://example.com/careers")
            assert len(jobs) >= 1
            assert jobs[0]["title"] == "Frontend Developer"

    @pytest.mark.unit
    async def test_scrape_source_playwright_fallback(self):
        """Should fall back to Playwright when httpx fails."""
        mock_html = """
        <html><body>
        <div class="job-listing">
            <a href="/jobs/pw1">Playwright Job</a>
        </div>
        </body></html>
        """

        with patch("app.services.scraper._wait_for_rate_limit", new_callable=AsyncMock), \
             patch("app.services.scraper.asyncio.sleep", new_callable=AsyncMock), \
             patch("app.services.scraper.httpx.AsyncClient") as mock_client_cls, \
             patch("app.services.scraper._fetch_with_playwright", new_callable=AsyncMock) as mock_pw:

            # httpx fails
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            # Playwright succeeds
            mock_pw.return_value = mock_html

            jobs = await scrape_source("https://example.com/careers")
            assert len(jobs) >= 1
            assert jobs[0]["title"] == "Playwright Job"
            mock_pw.assert_called_once()

    @pytest.mark.unit
    async def test_scrape_source_both_fail(self):
        """Should raise RuntimeError when both httpx and Playwright fail."""
        with patch("app.services.scraper._wait_for_rate_limit", new_callable=AsyncMock), \
             patch("app.services.scraper.asyncio.sleep", new_callable=AsyncMock), \
             patch("app.services.scraper.httpx.AsyncClient") as mock_client_cls, \
             patch("app.services.scraper._fetch_with_playwright", new_callable=AsyncMock) as mock_pw:

            # httpx fails
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            # Playwright also fails
            mock_pw.return_value = None

            with pytest.raises(RuntimeError, match="Failed to fetch"):
                await scrape_source("https://example.com/careers")

    @pytest.mark.unit
    async def test_scrape_source_blocked_page_triggers_fallback(self):
        """Should try Playwright when httpx returns a blocked-looking page."""
        blocked_html = "<html><body>Please complete the CAPTCHA</body></html>"
        good_html = """
        <html><body>
        <div class="job-listing">
            <a href="/jobs/real">Real Job</a>
        </div>
        </body></html>
        """

        mock_response = MagicMock()
        mock_response.text = blocked_html
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.scraper._wait_for_rate_limit", new_callable=AsyncMock), \
             patch("app.services.scraper.asyncio.sleep", new_callable=AsyncMock), \
             patch("app.services.scraper.httpx.AsyncClient") as mock_client_cls, \
             patch("app.services.scraper._fetch_with_playwright", new_callable=AsyncMock) as mock_pw:

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            mock_pw.return_value = good_html

            jobs = await scrape_source("https://example.com/careers")
            mock_pw.assert_called_once()
            assert len(jobs) >= 1
            assert jobs[0]["title"] == "Real Job"
