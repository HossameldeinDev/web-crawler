# AsyncWebCrawler

This project implements an asynchronous web crawler that uses `aiohttp` and `BeautifulSoup` for performing concurrent web requests and parsing HTML, respectively. It's designed to efficiently crawl websites and extract all internal links starting from a given base URL.

## Setup Instructions

### Creating and Activating a Virtual Environment

To create a virtual environment, which allows you to manage separate package installations for different projects, use the following commands:

```bash
# Create a virtual environment named 'venv'
python -m venv venv
# Activate the virtual environment
# On macOS and Linux
source venv/bin/activate
```
### Installing Dependencies
With the virtual environment activated, install the project dependencies with pip using the `requirements.txt` file:
#### Install dependencies
```bash
pip install -r requirements.txt
```
#### Running the Crawler

```bash
python main.py                                                                                                                                     ✔  web-crawler   03:36:27 AM 
Enter the URL to crawl (default 'https://monzo.com/'):
Enter the number of concurrent jobs (default 25):
```
The crawler will log the visiting URL and the urls in this page into bash and save it in .log file in logs directory.
#### Testing the Crawler
```bash
pytest --cov=crawler tests/ --cov-report term-missing
```
Currently, the test coverage is 100%.

### Workflow Steps

1. **Initialization**: The crawler is initialized with a base URL which is normalized for consistency. A queue is prepared for URLs to visit, and a concurrency limit is established to control the number of parallel tasks.

2. **Starting the Crawl**: Using the `crawl` method, the process begins by launching worker tasks up to the concurrency limit. These workers are responsible for asynchronously processing URLs from the queue.

3. **URL Fetching**: The `fetch` method is invoked by workers to make HTTP GET requests to the URLs. It ensures non-blocking operations and handles HTTP responses to retrieve the content.

4. **Content Handling and Parsing**: If the content type of the response is HTML, the crawler parses it to extract links. This is done using the `BeautifulSoup` library, which enables the crawler to find all hyperlinks on a page.

5. **Enqueuing New URLs**: Links found in the page's content are normalized and checked against the base domain to ensure they match the same subdomain. Valid links are enqueued, taking care to avoid duplicates and revisits.

6. **Concurrency and Throttling**: Concurrency is managed with `asyncio`, permitting the crawler to fetch multiple pages simultaneously. The crawler employs exponential back-off for retrying failed requests.

7. **Error Handling and Logging**: Comprehensive error handling is integrated to log various HTTP and network errors, as well as unexpected exceptions, aiding in progress monitoring and issue diagnosis.

8. **Resource Cleanup**: In all scenarios, the crawler ensures proper closure of network connections and cleanup of resources. This is facilitated by the use of `async with` statements and structured exception handling.

9. **Termination**: The crawler concludes its operation by ensuring all tasks have been processed. It then cancels any remaining tasks and closes the session gracefully.

The workflow is designed to be clear and efficient, handling various aspects of web crawling in a manner that ensures data integrity and respects server resources.
