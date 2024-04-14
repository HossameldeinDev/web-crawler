import logging
import os
import time
from urllib.parse import urlparse


def setup_logging(base_url):
    # Ensure the 'logs' directory exists
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Get current time as a formatted string
    current_time = time.strftime("%d-%m-%Y_%H:%M:%S")
    # Parse and sanitize the base URL to create a valid filename
    parsed_url = urlparse(base_url)
    domain = parsed_url.netloc
    # Set up filename for the log within the logs directory
    log_filename = f"{log_directory}/{current_time}-crawler_{domain}.log"

    # Configure logging to file and console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],
    )
