import pytest

from crawler.crawler import AsyncWebCrawler
from crawler.utils import normalize_url, parse_links


@pytest.mark.parametrize(
    "input_url,expected",
    [
        ("https://example.com", "https://example.com/"),
        ("http://example.com/some/page", "https://example.com/some/page"),
        ("https://EXAMPLE.COM/TEST?query=string", "https://example.com/TEST"),
    ],
)
def test_normalize_url(input_url: str, expected: str) -> None:
    assert normalize_url(input_url) == expected


@pytest.mark.asyncio
async def test_parse_links(crawler: AsyncWebCrawler, mock_html_content: str) -> None:
    # Call the parse_links method with mock HTML content
    links = await parse_links(crawler.base_url, mock_html_content)

    # Check the output of the parse_links method
    assert "https://example.com/page1.html" in links
    assert "https://example.com/page2.html" in links
    assert "https://community.example.com/page3.html" in links
