"""
Apify scraper integration for fetching website content.
"""
import logging
from apify_client import ApifyClient

logger = logging.getLogger(__name__)


def fetch_website_apify(url: str, api_key: str, max_pages: int = 5, timeout: int = 60) -> str:
    """
    Fetch website content using Apify web scraper actor.
    
    Args:
        url: Website URL to scrape
        api_key: Apify API key
        max_pages: Maximum pages to crawl (default: 5)
        timeout: Request timeout in seconds
        
    Returns:
        HTML content from scraped page
        
    Raises:
        Exception: If scraping fails
    """
    try:
        logger.info(f"Fetching {url} via Apify (max {max_pages} pages)...")
        
        client = ApifyClient(api_key)
        
        # Run the web scraper actor with proper configuration
        run_input = {
            "startUrls": [{"url": url}],
            "maxPagesPerCrawl": max_pages,
            "useChrome": True,
            "pageLoadTimeoutSecs": timeout,
            # Enable link following for multi-page crawling
            "linkSelector": "a",  # Follow all <a> tags
            "crawlRelativeUrls": True,  # Follow relative URLs on same domain
            # Custom headers to bypass tunnel/proxy warning pages
            # Using non-browser User-Agent: localtunnel bypasses tunnel reminder for non-browser requests
            # (webhooks, IPNs, curl, etc. are tunneled directly without the warning page)
            "customHeaders": {
                "bypass-tunnel-reminder": "true",  # Explicit bypass header (any value works)
                "User-Agent": "curl/7.64.1"  # Non-browser UA - bypasses tunnel reminder completely
            },
            # pageFunction that returns the HTML content and enqueues links
            "pageFunction": """async function pageFunction(context) {
                // Apify provides jQuery (via Cheerio) in the context
                const { enqueueRequest, jQuery, request } = context;
                
                try {
                    const $ = jQuery;
                    
                    // Enqueue links for crawling (follow internal links)
                    if (enqueueRequest) {
                        const links = $('a[href]').get().slice(0, 5);  // Get up to 5 links per page
                        for (const link of links) {
                            const href = $(link).attr('href');
                            if (href) {
                                try {
                                    await enqueueRequest({
                                        url: new URL(href, request.loadedUrl).href,
                                    });
                                } catch (e) {
                                    // Skip invalid URLs
                                }
                            }
                        }
                    }
                    
                    // Extract HTML content
                    let html = null;
                    if ($) {
                        html = $.html && $.html() || null;
                        if (!html) html = $('html').html() || null;
                        if (!html) html = $('body').html() || null;
                        if (!html) html = $.text && $.text() || '';
                    }
                    
                    return {
                        url: request.url,
                        loadedUrl: request.loadedUrl,
                        html: html || 'NO_HTML_EXTRACTED',
                    };
                } catch (e) {
                    return {
                        url: request.url,
                        html: '',
                        error: e.message
                    };
                }
            }"""
        }
        
        # Call the actor
        logger.info("Starting Apify web scraper actor...")
        actor_call = client.actor("apify/web-scraper").call(run_input=run_input)
        
        logger.info(f"Actor completed with run ID: {actor_call['id']}")
        
        # Retrieve the results from the dataset
        dataset = client.dataset(actor_call["defaultDatasetId"])
        items = list(dataset.iterate_items())
        
        if not items:
            logger.error("No data returned from Apify")
            return ""
        
        logger.info(f"Retrieved {len(items)} items from Apify")
        
        # Debug: Log item structure
        if items:
            logger.debug(f"First item keys: {list(items[0].keys())}")
            for key, value in items[0].items():
                if isinstance(value, str):
                    logger.debug(f"  {key}: {value[:100] if len(value) > 100 else value}")
                elif isinstance(value, dict):
                    logger.debug(f"  {key}: dict with keys {list(value.keys())[:5]}")
                else:
                    logger.debug(f"  {key}: {type(value).__name__}")
        
        # Apify's default output includes HTML and other metadata
        # Let's try to extract HTML from the items
        html_contents = []
        for idx, item in enumerate(items, 1):
            html_content = None
            
            # Try different possible locations for HTML content
            if isinstance(item, dict):
                # Check common Apify output fields
                if "html" in item:
                    html_content = item["html"]
                elif "body" in item:
                    html_content = item["body"]
                elif "content" in item:
                    html_content = item["content"]
                else:
                    # If none of the above, log what we got
                    logger.debug(f"Item {idx} structure: {list(item.keys())[:10]}")  # Log first 10 keys
            
            if html_content:
                html_contents.append(html_content)
                logger.info(f"Page {idx}: Retrieved {len(html_content)} chars")
            else:
                logger.warning(f"Page {idx}: Could not find HTML content in item")
        
        if not html_contents:
            logger.error(f"Could not extract HTML from {len(items)} items. Item structure: {items[0] if items else 'empty'}")
            # Return empty string instead of crashing
            return ""
        
        combined_html = "\n".join(html_contents)
        logger.info(f"Successfully scraped {len(items)} pages, total: {len(combined_html)} bytes")
        
        return combined_html
        
    except Exception as e:
        logger.error(f"Apify scraping failed: {str(e)}")
        raise
