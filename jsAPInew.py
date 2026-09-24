import asyncio
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from urllib.parse import urljoin

async def determine_if_js_heavy(url):
    """
    Determines if a website is JavaScript-heavy by comparing raw HTML content
    with rendered content length.
    
    Args:
        url (str): The URL to check
        
    Returns:
        dict: Results containing is_js_heavy status and details
    """
    result = {
        "is_js_heavy": False,
        "raw_html_size": 0,
        "rendered_html_size": 0,
        "ratio": 0
    }
    
    try:
        # Get raw HTML without JavaScript
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                raw_html = await response.text()
                result["raw_html_size"] = len(raw_html)
        
        # Get rendered HTML with JavaScript
        rendered_html = await render_with_playwright(url)
        if rendered_html:
            result["rendered_html_size"] = len(rendered_html)
            
            # Calculate ratio
            if result["raw_html_size"] > 0:
                result["ratio"] = result["rendered_html_size"] / result["raw_html_size"]
                result["is_js_heavy"] = result["ratio"] > 1.5
                
    except Exception as e:
        print(f"[JS Heavy Check Error] {str(e)}")
        
    return result

async def render_with_playwright(url, timeout=30000):
    """
    Renders a webpage using Playwright with JavaScript enabled.
    
    Args:
        url (str): The URL to render
        timeout (int): Maximum time to wait for page load in ms
        
    Returns:
        str: The rendered HTML content or None if failed
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Set default timeout for navigation
            page.set_default_timeout(timeout)
            
            # Wait for network to be idle to ensure JS has loaded
            await page.goto(url, wait_until="networkidle")
            
            # Get the rendered content
            content = await page.content()
            
            # Clean up
            await browser.close()
            return content
            
    except Exception as e:
        print(f"[Playwright Render Error] {str(e)}")
        return None

async def check_for_rss_feeds(url):
    """
    Checks a website for RSS feed links.
    
    Args:
        url (str): The URL to check
        
    Returns:
        list: List of RSS feed URLs found
    """
    rss_feeds = []
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                html = await response.text()
        
        # Parse HTML and look for RSS links
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check link tags with RSS type
        feed_links = soup.find_all("link", type="application/rss+xml")
        for link in feed_links:
            href = link.get("href")
            if href:
                # Handle relative URLs
                full_url = urljoin(url, href)
                rss_feeds.append(full_url)
        
        # Also check for alternate links with RSS type
        alternate_links = soup.find_all("link", rel="alternate")
        for link in alternate_links:
            if link.get("type") in ["application/rss+xml", "application/atom+xml"]:
                href = link.get("href")
                if href:
                    full_url = urljoin(url, href)
                    if full_url not in rss_feeds:
                        rss_feeds.append(full_url)
                        
    except Exception as e:
        print(f"[RSS Feed Check Error] {str(e)}")
        
    return rss_feeds

async def check_for_open_apis(url):
    """
    Checks a website for open API endpoints.
    
    Args:
        url (str): The URL to check
        
    Returns:
        list: List of potential API endpoints found
    """
    api_endpoints = []
    common_paths = [
        "/api",
        "/api/v1",
        "/api/v2",
        "/api-docs",
        "/swagger",
        "/swagger-ui",
        "/swagger-ui.html",
        "/openapi.json",
        "/graphql",
        "/wp-json",      # WordPress REST API
        "/rest"          # Common REST endpoint
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            # Check all potential API paths concurrently
            tasks = []
            for path in common_paths:
                test_url = url.rstrip("/") + path
                tasks.append(_check_api_endpoint(session, test_url))
                
            # Gather results
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            for endpoint in results:
                if endpoint and endpoint not in api_endpoints:
                    api_endpoints.append(endpoint)
                    
    except Exception as e:
        print(f"[API Check Error] {str(e)}")
        
    return api_endpoints

async def _check_api_endpoint(session, url):
    """
    Checks if a specific URL is a valid API endpoint.
    
    Args:
        session (aiohttp.ClientSession): The HTTP session to use
        url (str): The URL to check
        
    Returns:
        str: The URL if it's a valid API endpoint, None otherwise
    """
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                content_type = response.headers.get("Content-Type", "").lower()
                content = await response.text()
                
                # Check if it's likely to be an API
                if any(t in content_type for t in ["json", "application/openapi", "swagger"]):
                    return url
                    
                # Check content for JSON structure
                content_sample = content[:1000].strip()
                if content_sample and (
                    (content_sample.startswith('{') and content_sample.endswith('}')) or
                    (content_sample.startswith('[') and content_sample.endswith(']'))
                ):
                    return url
                    
    except Exception:
        pass
        
    return None

async def analyze_website(url):
    """
    Main function to analyze a website for JavaScript heaviness, RSS feeds, and APIs.
    
    Args:
        url (str): The URL to analyze
        
    Returns:
        dict: Analysis results
    """
    # Run all checks concurrently
    js_heavy_task = determine_if_js_heavy(url)
    rss_task = check_for_rss_feeds(url)
    api_task = check_for_open_apis(url)
    
    # Wait for all tasks to complete
    js_heavy_result, rss_feeds, api_endpoints = await asyncio.gather(
        js_heavy_task, rss_task, api_task
    )
    
    # Compile results
    results = {
        "url": url,
        "js_heavy": js_heavy_result,
        "rss_feeds": rss_feeds,
        "api_endpoints": api_endpoints
    }
    
    return results

# Example usage
async def maina(lnk):
    # urls = [
    #     "https://example.com",
    #     "https://news.ycombinator.com",
    #     "https://reuters.com",
    #     "https://instagram.com",
    #     "https://youtube.com"
    #     # Add more URLs as needed
    # ]
    
    urls = []
    urls.append(lnk)
    
    # Analyze all URLs concurrently
    tasks = [analyze_website(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    # Display results
    for result in results:
        url = result["url"]
        print(f"\nResults for {url}:")
        print(f"JavaScript Heavy: {result['js_heavy']['is_js_heavy']} (Ratio: {result['js_heavy']['ratio']:.2f})")
        print(f"RSS Feeds: {result['rss_feeds'] if result['rss_feeds'] else 'None found'}")
        print(f"API Endpoints: {result['api_endpoints'] if result['api_endpoints'] else 'None found'}")

async def maino(url):
    # Process a single URL from the parameter
    result = await analyze_website(url)
    
    # Display results
    print(f"\nResults for {url}:")
    print(f"JavaScript Heavy: {result['js_heavy']['is_js_heavy']} (Ratio: {result['js_heavy']['ratio']:.2f})")
    print(f"RSS Feeds: {result['rss_feeds'] if result['rss_feeds'] else 'None found'}")
    print(f"API Endpoints: {result['api_endpoints'] if result['api_endpoints'] else 'None found'}")
    
    # Return the result in case it's needed elsewhere
    #return result

if __name__ == "__main__":
    asyncio.run(maina())