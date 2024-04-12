import asyncio
import logging

from crawler.crawler import AsyncWebCrawler

if __name__ == "__main__":
    import time

    start_time = time.time()
    # crawler = AsyncWebCrawler("https://monzo.com/", concurrency=10)
    crawler = AsyncWebCrawler("https://books.toscrape.com/", concurrency=10)
    asyncio.run(crawler.crawl())
    end_time = time.time()
    logging.info(f"Running time: {end_time - start_time} seconds")
