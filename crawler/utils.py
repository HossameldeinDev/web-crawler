from urllib.parse import urlparse, urlunparse


def normalize_url(url):
    parsed_url = urlparse(url)
    scheme = "https"
    netloc = parsed_url.netloc.lower()
    path = parsed_url.path if parsed_url.path else "/"
    normalized_url = urlunparse((scheme, netloc, path, "", "", ""))
    return normalized_url
