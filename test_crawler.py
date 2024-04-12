from crawler import AsyncWebCrawler, normalize_url
from unittest.mock import MagicMock
import pytest
from aiohttp import ClientSession
from unittest.mock import patch, AsyncMock
import asyncio


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


@pytest.mark.asyncio
async def test_fetch_non_html_content():
    crawler = AsyncWebCrawler("https://example.com")
    url = "https://example.com/data"

    # Mock response to simulate non-HTML content
    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_response.text = AsyncMock(return_value='{"key": "value"}')

    # Set up context manager mock
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    # Mock ClientSession.get
    with patch('aiohttp.ClientSession.get', return_value=mock_context_manager):
        async with ClientSession() as session:
            with patch('logging.info') as mock_log:
                await crawler.fetch(session, url)
                mock_log.assert_called_with("Skipping non-HTML content: https://example.com/data")


@pytest.mark.asyncio
async def test_fetch_with_network_errors_and_retries():
    crawler = AsyncWebCrawler("https://example.com")
    url = "https://example.com/fail"

    # Set up a response to raise an exception
    mock_response = AsyncMock(side_effect=Exception("Connection error"))

    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(side_effect=Exception("Connection error"))
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    with patch('aiohttp.ClientSession.get', return_value=mock_context_manager):
        async with ClientSession() as session:
            with patch('logging.warning') as mock_log_warning, patch('asyncio.sleep',
                                                                     new_callable=AsyncMock) as mock_sleep:
                await crawler.fetch(session, url)
                assert mock_log_warning.call_count == 3  # Assuming 3 retries
                assert mock_sleep.await_count == 2  # Sleep between retries


@pytest.mark.asyncio
async def test_parse_and_enqueue_links():
    crawler = AsyncWebCrawler("https://example.com")
    base_url = "https://example.com/"
    html_content = "<html><a href='page1.html'>Page 1</a><a href='https://example.com/page2.html'>Page 2</a></html>"

    # Clear the queue before the test
    while not crawler.urls_to_visit.empty():
        await crawler.urls_to_visit.get()

    # Use actual session in the test
    async with ClientSession() as session:
        await crawler.parse_links(session, base_url, html_content)
        first_url = await crawler.urls_to_visit.get()
        second_url = await crawler.urls_to_visit.get()
        assert first_url == "https://example.com/page1.html"
        assert second_url == "https://example.com/page2.html"
        assert crawler.urls_to_visit.empty()


@pytest.mark.asyncio
async def test_crawl_execution():
    crawler = AsyncWebCrawler("https://example.com")

    # Prepopulate the queue with a URL and immediately set it as visited to simulate quick depletion
    await crawler.urls_to_visit.put("https://example.com/page")
    crawler.visited_urls.add("https://example.com/page")

    # Mock the worker to immediately mark the queue task as done
    async def mock_worker(session):
        while True:
            try:
                url = await crawler.urls_to_visit.get()
                crawler.urls_to_visit.task_done()
                break  # Break after processing one URL to prevent hanging
            except asyncio.CancelledError:
                break  # Ensure workers stop on cancellation

    # Replace the original worker with the mock
    crawler.worker = mock_worker

    # Run the crawler
    await crawler.crawl()

    # Check that the queue is empty and has been joined
    assert crawler.urls_to_visit.empty()
    # This line asserts that all tasks are indeed completed
    assert crawler.urls_to_visit._unfinished_tasks == 0
