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
