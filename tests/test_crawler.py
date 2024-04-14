from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession


def test_crawler_initialization(crawler):
    assert crawler.base_url == "https://example.com/"
    assert crawler.base_domain == "example.com"
    assert crawler.concurrency == 5
    assert crawler.urls_to_visit.qsize() == 1


@pytest.mark.asyncio
async def test_fetch_html_content(
    crawler,
    mock_html_response,
    mock_context_manager_factory,
):
    # Use the factory to create a context manager with the mock HTML response
    mock_context_manager = mock_context_manager_factory(
        mock_response=mock_html_response,
    )
    with patch("aiohttp.ClientSession.get", return_value=mock_context_manager):
        async with ClientSession() as session:
            await crawler.fetch(session, crawler.base_url)
            # Check that text method is called to fetch HTML content
            mock_html_response.text.assert_called_once()
            # Ensure that the queue size has increased as the link should be added
            assert crawler.urls_to_visit.qsize() == 3
            # Verify that the correct URL is queued
            all_urls = []
            while not crawler.urls_to_visit.empty():
                all_urls.append(await crawler.urls_to_visit.get())
            assert "https://example.com/page1.html" in all_urls
            assert "https://example.com/" in all_urls
            assert "https://example.com/page2.html" in all_urls
            assert "https://community.example.com/page3.html" not in all_urls


@pytest.mark.asyncio
async def test_fetch_non_html_content(
    crawler,
    mock_non_html_response,
    mock_context_manager_factory,
):
    mock_context_manager = mock_context_manager_factory(
        mock_response=mock_non_html_response,
    )
    # Mock ClientSession.get
    with patch("aiohttp.ClientSession.get", return_value=mock_context_manager):
        async with ClientSession() as session:
            with patch("logging.info") as mock_log:
                await crawler.fetch(session, crawler.base_url)
                mock_log.assert_called_with(
                    "Skipping non-HTML content: https://example.com/",
                )


@pytest.mark.asyncio
async def test_fetch_with_network_errors_and_retries(
    crawler,
    mock_context_manager_factory,
):
    mock_context_manager = mock_context_manager_factory(
        side_effect=Exception("Connection error"),
    )
    with patch("aiohttp.ClientSession.get", return_value=mock_context_manager):
        async with ClientSession() as session:
            with patch("logging.warning") as mock_log_warning, patch(
                "asyncio.sleep",
                new_callable=AsyncMock,
            ) as mock_sleep:
                await crawler.fetch(session, crawler.base_url)
                assert mock_log_warning.call_count == 3  # Assuming 3 retries
                assert mock_sleep.await_count == 2  # Sleep between retries


@pytest.mark.asyncio
async def test_crawl_execution(crawler, mock_worker):
    # Prepopulate the queue with a URL and immediately set it as visited to simulate quick depletion
    await crawler.urls_to_visit.put("https://example.com/page")
    crawler.visited_urls.add("https://example.com/page")
    # Run the crawler
    await crawler.crawl()
    # Check that the queue is empty and has been joined
    assert crawler.urls_to_visit.empty()
    # This line asserts that all tasks are indeed completed
    assert crawler.urls_to_visit._unfinished_tasks == 0
