from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientConnectionError, ClientResponseError, ClientSession

from crawler.crawler import AsyncWebCrawler


def test_crawler_initialization(crawler: AsyncWebCrawler) -> None:
    assert crawler.base_url == "https://example.com/"
    assert crawler.base_domain == "example.com"
    assert crawler.concurrency == 5
    assert crawler.urls_to_visit.qsize() == 1


@pytest.mark.asyncio
async def test_fetch_html_content(
    crawler: AsyncWebCrawler,
    mock_html_response: str,
    mock_context_manager_factory: Callable[[Any, Any], MagicMock],
) -> None:
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
    crawler: AsyncWebCrawler,
    mock_non_html_response: str,
    mock_context_manager_factory: Callable[[Any, Any], MagicMock],
) -> None:
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
    crawler: AsyncWebCrawler,
    mock_context_manager_factory: Callable[[Any, Any], MagicMock],
) -> None:
    connection_error = ClientConnectionError("Connection error")
    mock_context_manager = mock_context_manager_factory(
        side_effect=connection_error,
    )
    with patch("aiohttp.ClientSession.get", return_value=mock_context_manager):
        async with ClientSession() as session:
            with patch("logging.warning") as mock_log_warning, patch(
                "logging.error",
            ) as mock_log_error, patch(
                "asyncio.sleep",
                new_callable=AsyncMock,
            ) as mock_sleep:
                await crawler.fetch(session, crawler.base_url)
                # Error log should be called once after all retries have been exhausted
                assert mock_log_error.call_count == 1
                # Sleep should be called twice between the retries
                assert mock_sleep.await_count == 2


@pytest.mark.asyncio
async def test_fetch_404_client_error(
    crawler: AsyncWebCrawler,
    mock_context_manager_factory: Callable[[Any, Any], MagicMock],
) -> None:
    # Simulate a 404 client error
    client_error = ClientResponseError(
        request_info=None,
        history=(),
        status=404,
        message="Not Found",
        headers=None,
    )
    mock_context_manager = mock_context_manager_factory(
        side_effect=client_error,
    )
    with patch("aiohttp.ClientSession.get", return_value=mock_context_manager):
        async with ClientSession() as session:
            with patch("logging.warning") as mock_log_warning:
                await crawler.fetch(session, crawler.base_url)
                # Check that the warning is logged once for the 404 error
                mock_log_warning.assert_called_once_with(
                    f"URL not found: {crawler.base_url}",
                )
                # Ensure no retries for 404 client error
                assert mock_log_warning.call_count == 1


@pytest.mark.asyncio
async def test_fetch_unhandled_exception(
    crawler: AsyncWebCrawler,
    mock_context_manager_factory: Callable[[Any, Any], MagicMock],
) -> None:
    # Simulate an unhandled exception
    unhandled_exception = Exception("Unhandled error occurred")
    mock_context_manager = mock_context_manager_factory(
        side_effect=unhandled_exception,
    )
    with patch("aiohttp.ClientSession.get", return_value=mock_context_manager):
        async with ClientSession() as session:
            with patch("logging.error") as mock_log_error:
                await crawler.fetch(session, crawler.base_url)
                # Check that the error is logged once for the unhandled exception
                mock_log_error.assert_called_once_with(
                    f"Unhandled exception for {crawler.base_url}: {unhandled_exception}",
                )
                # Ensure no retries for unhandled exceptions
                assert mock_log_error.call_count == 1


@pytest.mark.asyncio
async def test_fetch_client_error_non_403(
    crawler: AsyncWebCrawler,
    mock_context_manager_factory: Callable[[Any, Any], MagicMock],
) -> None:
    # Simulate a 403 client error
    client_error = ClientResponseError(
        request_info=None,
        history=(),
        status=403,
        message="Forbidden",
        headers=None,
    )
    mock_context_manager = mock_context_manager_factory(
        side_effect=client_error,
    )
    with patch("aiohttp.ClientSession.get", return_value=mock_context_manager):
        async with ClientSession() as session:
            with patch("logging.warning") as mock_log_warning:
                await crawler.fetch(session, crawler.base_url)
                # Check that the warning is logged once for the 403 error
                mock_log_warning.assert_called_once_with(
                    f"Client error 403 for {crawler.base_url}: Forbidden",
                )
                # Ensure no retries for client errors other than network related
                assert mock_log_warning.call_count == 1


@pytest.mark.asyncio
async def test_crawl_execution(crawler: AsyncWebCrawler, mock_worker: Callable) -> None:
    # Prepopulate the queue with a URL and immediately set it as visited to simulate quick depletion
    await crawler.urls_to_visit.put("https://example.com/page")
    crawler.visited_urls.add("https://example.com/page")
    # Run the crawler
    await crawler.crawl()
    # Check that the queue is empty and has been joined
    assert crawler.urls_to_visit.empty()
    # This line asserts that all tasks are indeed completed
    assert crawler.urls_to_visit._unfinished_tasks == 0
