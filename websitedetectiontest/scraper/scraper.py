"""
ScraperAPI wrapper for fetching website content.
"""
import requests
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ScraperAPIClient:
    """Client for ScraperAPI to fetch website content."""
    
    BASE_URL = "http://api.scraperapi.com"
    
    def __init__(self, api_key: str):
        """
        Initialize ScraperAPI client.
        
        Args:
            api_key: ScraperAPI key for authentication
        """
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key
    
    def fetch_website(self, url: str, timeout: int = 30, locale: str = 'en-US', render: bool = True) -> Optional[str]:
        """
        Fetch website content using ScraperAPI.
        
        Args:
            url: Website URL to fetch
            timeout: Request timeout in seconds
            locale: Browser locale (default: en-US for English)
            render: Enable JavaScript rendering (default: True for better content capture)
            
        Returns:
            Raw HTML content if successful, None otherwise
            
        Raises:
            ValueError: If URL is invalid
            requests.RequestException: If API call fails
        """
        if not url:
            raise ValueError("URL is required")
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # For rendering, use root URL only (SPA support)
        # This prevents 404 errors on routes like /about in single-page apps
        fetch_url = url
        if render:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            fetch_url = f"{parsed.scheme}://{parsed.netloc}"
            if url != fetch_url:
                logger.info(f"Using root URL for SPA rendering: {fetch_url} (original: {url})")
        
        params = {
            'api_key': self.api_key,
            'url': fetch_url,
            'locale': locale,  # Request English content
            'render': 'true' if render else 'false'  # Enable/disable JavaScript rendering
        }
        
        # Set browser headers to mimic real browser
        headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            render_status = "with JS rendering" if render else "without JS rendering"
            logger.info(f"Fetching {url} via ScraperAPI (locale={locale}, {render_status})...")
            response = requests.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            
            content = response.text
            if not content or len(content.strip()) == 0:
                logger.warning(f"Empty response for {url}")
                return None
            
            logger.info(f"Successfully fetched {len(content)} bytes from {url}")
            return content
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {url} (timeout={timeout}s)")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
            raise
