import logging
from typing import List
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup


def normalize_url(url: str) -> str:
    parsed_url = urlparse(url)
    scheme = "https"
    netloc = parsed_url.netloc.lower()
    path = parsed_url.path if parsed_url.path else "/"
    # urlunparse parameters are scheme, netloc, path, params, query, fragment and we intentionally remove the last three
    normalized_url = urlunparse((scheme, netloc, path, "", "", ""))
    return normalized_url


async def parse_links(full_url: str, html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    found_urls = [
        normalize_url(urljoin(full_url, link["href"]))
        for link in soup.find_all("a", href=True)
    ]
    logging.info(f"URLs found in: {full_url} : {found_urls}")
    return found_urls
