import asyncio
from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock

import pytest

from crawler.crawler import AsyncWebCrawler


@pytest.fixture
def crawler() -> AsyncWebCrawler:
    return AsyncWebCrawler("https://example.com", concurrency=5)


@pytest.fixture
def mock_html_content() -> str:
    return """
        <html>
            <body>
                <a href='page1.html'>Link to Same Domain</a>
                <a href='https://community.example.com/page3.html'>Link to Subdomain</a>
                <a href='https://example.com/page2.html'>Page 2</a></html>
            </body>
        </html>
        """


@pytest.fixture
def mock_html_response(mock_html_content: str) -> AsyncMock:
    response = AsyncMock()
    response.raise_for_status = AsyncMock()
    response.headers = {"Content-Type": "text/html; charset=utf-8"}
    response.text = AsyncMock(return_value=mock_html_content)
    return response


@pytest.fixture
def mock_non_html_response() -> AsyncMock:
    response = AsyncMock()
    response.raise_for_status = AsyncMock()
    response.headers = {"Content-Type": "application/json"}
    response.text = AsyncMock(return_value='{"key": "value"}')
    return response


@pytest.fixture
def mock_context_manager_factory() -> Callable[[Any, Any], MagicMock]:
    def _factory(mock_response: AsyncMock = None, side_effect: AsyncMock = None):
        # Create a context manager mock that uses the provided mock_response or side_effect
        context_manager = MagicMock()
        if side_effect:
            # Simulate an exception if side_effect is provided
            context_manager.__aenter__ = AsyncMock(side_effect=side_effect)
        else:
            # Return mock_response if no side_effect is provided
            context_manager.__aenter__ = AsyncMock(return_value=mock_response)

        context_manager.__aexit__ = AsyncMock(return_value=None)
        return context_manager

    return _factory


# Mock the worker to immediately mark the queue task as done
@pytest.fixture
async def mock_worker(crawler: AsyncWebCrawler) -> None:
    while True:
        try:
            await crawler.urls_to_visit.get()
            crawler.urls_to_visit.task_done()
            break  # Break after processing one URL to prevent hanging
        except asyncio.CancelledError:
            break  # Ensure workers stop on cancellation
