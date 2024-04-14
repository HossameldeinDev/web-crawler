import asyncio
import logging
from urllib.parse import urlparse

import aiohttp
from aiohttp import ClientTimeout

from crawler.utils import normalize_url, parse_links


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
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "text/html" in content_type:
                        logging.info(f"Visiting: {url}")
                        html = await response.text()
                        links = await parse_links(url, html)
                        await self.enqueue_urls(links)
                        return
                    else:
                        logging.info(f"Skipping non-HTML content: {url}")
                        return
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential back-off
                else:
                    logging.error(f"Failed to fetch {url} after {retries} attempts")

    async def enqueue_urls(self, links):
        for link in links:
            if urlparse(link).netloc.lower() == self.base_domain:
                async with self.lock:  # Prevent adding duplicates concurrently
                    if link not in self.visited_urls:
                        await self.urls_to_visit.put(link)
