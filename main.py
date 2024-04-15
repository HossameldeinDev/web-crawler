import asyncio
import logging
import time

from crawler.crawler import AsyncWebCrawler
from logging_conf import setup_logging

if __name__ == "__main__":
    url = (
        input("Enter the URL to crawl (default 'https://monzo.com/'): ")
        or "https://monzo.com/"
    )
    setup_logging(url)
    try:
        concurrency = int(
            input("Enter the number of concurrent jobs (default 5): ") or 5,
        )
    except ValueError:
        logging.error("Invalid input for concurrency, using default of 5.")
        concurrency = 5

    logging.info(f"Starting crawl at {url} with {concurrency} concurrent jobs.")

    start_time = time.time()
    crawler = AsyncWebCrawler(url, concurrency=concurrency)
    asyncio.run(crawler.crawl())
    end_time = time.time()

    logging.info(f"Running time: {end_time - start_time} seconds")
