from crawler import AsyncWebCrawler, normalize_url
from unittest.mock import AsyncMock
import pytest
from unittest.mock import patch, MagicMock
from aiohttp import ClientSession


@pytest.mark.parametrize("input_url,expected", [
    ("https://example.com", "https://example.com/"),
    ("http://example.com/some/page", "https://example.com/some/page"),
    ("https://EXAMPLE.COM/TEST?query=string", "https://example.com/TEST"),
])
def test_normalize_url(input_url, expected):
    assert normalize_url(input_url) == expected


def test_crawler_initialization():
    crawler = AsyncWebCrawler("https://example.com", concurrency=5)
    assert crawler.base_url == "https://example.com/"
    assert crawler.base_domain == "example.com"
    assert crawler.concurrency == 5
    assert crawler.urls_to_visit.qsize() == 1


@pytest.mark.asyncio
async def test_fetch_html_content():
    from crawler import AsyncWebCrawler  # Import your crawler

    # Create the crawler instance
    crawler = AsyncWebCrawler("https://example.com")
    url = "https://example.com/page"

    # Mock response setup
    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.headers = {'Content-Type': 'text/html; charset=utf-8'}
    mock_response.text = AsyncMock(return_value="<html><body><a href='page2.html'>Link</a></body></html>")

    # Mock context manager for the mock response
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    # Patch the ClientSession.get to return our mock context manager
    with patch('aiohttp.ClientSession.get', return_value=mock_context_manager):
        # Create a client session and pass it along with the URL to fetch method
        async with ClientSession() as session:
            with patch.object(crawler, 'parse_links', new_callable=AsyncMock) as mock_parse_links:
                await crawler.fetch(session, url)  # Corrected to pass both session and url
                mock_response.text.assert_called_once()
                mock_parse_links.assert_called_once()