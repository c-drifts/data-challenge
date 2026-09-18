"""Data loading utilities for fetching from APIs or local files"""

import pandas as pd
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_data(endpoint_url, fallback_file_path, format_type="csv", fallback_format=None):
    """
    Fetch data from an API endpoint with fallback to local file.

    Args:
        endpoint_url: URL of the API endpoint
        fallback_file_path: Path to local file if API fails
        format_type: Format of API response ('json' or 'csv')
        fallback_format: Format of fallback file (if different from API format)

    Returns:
        pd.DataFrame with the loaded data
    """
    try:
        logger.info(f"Fetching from {endpoint_url}")
        response = requests.get(endpoint_url, timeout=10)
        response.raise_for_status()
        return _parse_response(response, format_type)

    except Exception as e:
        logger.warning(f"Failed to fetch from API: {e}. Using fallback file: {fallback_file_path}")
        # Use fallback_format if specified, otherwise use format_type
        file_format = fallback_format if fallback_format else format_type
        return _load_local_file(fallback_file_path, file_format)


def _parse_response(response, format_type):
    """Parse API response based on format type"""
    if format_type.lower() == "json":
        if isinstance(data, dict) and "events" in data:
            return pd.DataFrame(response.json()["events"])
        return pd.DataFrame(response.json())
    elif format_type.lower() == "csv":
        from io import StringIO
        return pd.read_csv(StringIO(response.text))
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def _load_local_file(file_path, format_type):
    """Load data from local file"""
    if format_type.lower() == "json":
        return pd.read_json(file_path)
    elif format_type.lower() == "csv":
        return pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported format: {format_type}")


