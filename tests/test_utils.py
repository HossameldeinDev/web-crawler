import pytest

from crawler.utils import normalize_url


@pytest.mark.parametrize(
    "input_url,expected",
    [
        ("https://example.com", "https://example.com/"),
        ("http://example.com/some/page", "https://example.com/some/page"),
        ("https://EXAMPLE.COM/TEST?query=string", "https://example.com/TEST"),
    ],
)
def test_normalize_url(input_url, expected):
    assert normalize_url(input_url) == expected
