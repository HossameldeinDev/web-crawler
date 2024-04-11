import asyncio
import aiohttp
from urllib.parse import urlparse, urljoin, urlunparse
from aiohttp import ClientTimeout


class AsyncWebCrawler:
    def __init__(self, base_url):
        self.base_url = self.normalize_url(base_url)
        self.base_domain = urlparse(base_url).netloc.lower()
        self.visited_urls = set()
        self.urls_to_visit = {self.base_url}

    async def crawl(self):
        async with aiohttp.ClientSession() as session:
            # Initialize the semaphore with a specific concurrency limit, e.g., 10.
            sem = asyncio.Semaphore(10)
            tasks = []
            while self.urls_to_visit:
                url = self.urls_to_visit.pop()
                if url not in self.visited_urls and urlparse(url).netloc.lower() == self.base_domain:
                    # Pass the semaphore along with other necessary parameters.
                    task = asyncio.create_task(self.bounded_fetch(sem, session, url))
                    tasks.append(task)
                if len(tasks) >= 10 or not self.urls_to_visit:
                    await asyncio.gather(*tasks)
                    tasks = []
            if tasks:  # Ensure no task is left behind.
                await asyncio.gather(*tasks)

    async def bounded_fetch(self, sem, session, url):
        # Make sure to use the semaphore within an async with statement.
        async with sem:
            await self.fetch(session, url)

    async def fetch(self, session, url):
        try:
            # print("start: ", url)
            # Define a timeout for the request; adjust the seconds as needed
            timeout = ClientTimeout(total=10)  # 10 seconds timeout for the whole operation

            headers = {'User-Agent': 'MyCrawler/1.0 (mycrawler@example.com)'}
            # Include the timeout in the session.get call
            async with session.get(url, allow_redirects=True, headers=headers, timeout=timeout) as response:
                response.raise_for_status()  # This will raise an error for 4xx and 5xx status codes

                final_url = str(response.url)
                if 'text/html' in response.headers.get('Content-Type', '').lower():
                    if final_url not in self.visited_urls:
                        print(f"Visiting: {final_url}")
                        self.visited_urls.add(final_url)
                        await self.parse_links(session, final_url, await response.text())
                else:
                    print(f"Skipping non-HTML content: {final_url}")
        except asyncio.TimeoutError:
            print(f"Request timed out: {url}")
        except Exception as e:  # Catch other exceptions to prevent the crawler from stopping
            print(f"Error fetching {url}: {e}")

    async def parse_links(self, session, base_url, html):
        from bs4 import BeautifulSoup  # Import here to avoid unused import if not crawling HTML
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            full_url = self.normalize_url(urljoin(base_url, link['href']))
            # print(f"- {full_url}")
            if (urlparse(full_url).netloc.lower() == self.base_domain and
                    full_url not in self.visited_urls):
                self.urls_to_visit.add(full_url)
        # print("End: ", base_url)

    def normalize_url(self, url):
        parsed_url = urlparse(url)
        scheme = "https"  # Enforce HTTPS for all URLs
        netloc = parsed_url.netloc.lower()

        # Only add a trailing slash if the path is empty, indicating the root domain
        path = parsed_url.path
        if not path:
            path = "/"

        normalized_url = urlunparse((scheme, netloc, path, '', '', ''))
        return normalized_url


if __name__ == "__main__":
    crawler = AsyncWebCrawler("https://monzo.com/")
    # crawler = AsyncWebCrawler("https://books.toscrape.com/")
    asyncio.run(crawler.crawl())
