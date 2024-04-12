import asyncio
import logging
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientTimeout

from crawler.utils import normalize_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class AsyncWebCrawler:
    def __init__(self, base_url, concurrency=10):
        self.base_url = normalize_url(base_url)
        self.base_domain = urlparse(base_url).netloc.lower()
        self.visited_urls = set()
        self.urls_to_visit = asyncio.Queue()
        self.urls_to_visit.put_nowait(self.base_url)
        self.concurrency = concurrency
        self.lock = asyncio.Lock()  # Lock for visited_urls access

    async def crawl(self):
        async with aiohttp.ClientSession() as session:
            workers = [
                asyncio.create_task(self.worker(session))
                for _ in range(self.concurrency)
            ]
            await self.urls_to_visit.join()
            for worker in workers:
                worker.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

    async def worker(self, session):
        while True:
            try:
                url = await self.urls_to_visit.get()
                async with self.lock:  # Check and mark visited atomically
                    if url in self.visited_urls:
                        continue
                    self.visited_urls.add(url)
                await self.fetch(session, url)
            finally:
                self.urls_to_visit.task_done()

    async def fetch(self, session, url, retries=3):
        for attempt in range(retries):
            try:
                timeout = ClientTimeout(total=10)
                headers = {"User-Agent": "MyCrawler/1.0"}
                async with session.get(
                    url,
                    allow_redirects=True,
                    headers=headers,
                    timeout=timeout,
                ) as response:
                    response.raise_for_status()
                    if (
                        "text/html"
                        not in response.headers.get("Content-Type", "").lower()
                    ):
                        logging.info(f"Skipping non-HTML content: {url}")
                        return
                    logging.info(f"Visiting: {url}")
                    await self.parse_links(session, url, await response.text())
                    return
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2**attempt)
                else:
                    logging.error(f"Failed to fetch {url} after {retries} attempts")

    async def parse_links(self, session, base_url, html):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for link in soup.find_all("a", href=True):
            full_url = normalize_url(urljoin(base_url, link["href"]))
            if urlparse(full_url).netloc.lower() == self.base_domain:
                async with self.lock:  # Prevent adding duplicates concurrently
                    if full_url not in self.visited_urls:
                        await self.urls_to_visit.put(full_url)
