"""
Browser Operations

Control web browsers programmatically using Playwright.
Supports Chrome, Firefox, and Edge.

Requirements:
    pip install playwright
    playwright install
"""

import os
import subprocess
from typing import Optional, Dict, Any, List
from zenus_core.tools.base import Tool


class BrowserOps(Tool):
    """
    Web browser automation and control
    
    Capabilities:
    - Open URLs in browser
    - Navigate and interact with pages
    - Take screenshots
    - Extract page content
    - Fill forms and click elements
    - Execute JavaScript
    """
    
    def __init__(self):
        self.playwright_installed = self._check_playwright()
    
    def _check_playwright(self) -> bool:
        """Check if Playwright is installed"""
        try:
            import playwright
            return True
        except ImportError:
            return False
    
    def _ensure_playwright(self):
        """Ensure Playwright is available"""
        if not self.playwright_installed:
            raise RuntimeError(
                "Playwright not installed.\n"
                "Install with: pip install playwright && playwright install"
            )
    
    def open(self, url: str, browser: str = "chromium", headless: bool = False) -> str:
        """
        Open URL in browser
        
        Args:
            url: URL to open
            browser: Browser to use (chromium, firefox, webkit)
            headless: Run in headless mode (no GUI)
        
        Returns:
            Success message
        """
        self._ensure_playwright()
        
        from playwright.sync_api import sync_playwright
        
        try:
            with sync_playwright() as p:
                # Launch browser
                if browser == "chromium":
                    browser_instance = p.chromium.launch(headless=headless)
                elif browser == "firefox":
                    browser_instance = p.firefox.launch(headless=headless)
                elif browser == "webkit":
                    browser_instance = p.webkit.launch(headless=headless)
                else:
                    return f"Error: Unknown browser '{browser}'"
                
                # Open page
                page = browser_instance.new_page()
                page.goto(url)
                
                title = page.title()
                
                # Keep browser open if not headless
                if not headless:
                    page.wait_for_timeout(2000)  # Wait 2s for user to see
                
                browser_instance.close()
                
                return f"Opened {url} in {browser}. Page title: {title}"
        
        except Exception as e:
            return f"Error opening browser: {str(e)}"
    
    def screenshot(
        self, 
        url: str, 
        output_path: str, 
        browser: str = "chromium",
        full_page: bool = False
    ) -> str:
        """
        Take screenshot of webpage
        
        Args:
            url: URL to screenshot
            output_path: Path to save screenshot
            browser: Browser to use
            full_page: Capture full scrollable page
        
        Returns:
            Path to screenshot
        """
        self._ensure_playwright()
        
        from playwright.sync_api import sync_playwright
        
        try:
            with sync_playwright() as p:
                # Launch browser
                if browser == "chromium":
                    browser_instance = p.chromium.launch(headless=True)
                elif browser == "firefox":
                    browser_instance = p.firefox.launch(headless=True)
                else:
                    browser_instance = p.webkit.launch(headless=True)
                
                page = browser_instance.new_page()
                page.goto(url)
                page.wait_for_load_state("networkidle")
                
                # Expand path
                output_path = os.path.expanduser(output_path)
                
                # Take screenshot
                page.screenshot(path=output_path, full_page=full_page)
                
                browser_instance.close()
                
                return f"Screenshot saved to {output_path}"
        
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"
    
    def get_text(self, url: str, selector: Optional[str] = None) -> str:
        """
        Extract text from webpage
        
        Args:
            url: URL to extract from
            selector: CSS selector (optional, gets all text if None)
        
        Returns:
            Extracted text
        """
        self._ensure_playwright()
        
        from playwright.sync_api import sync_playwright
        
        try:
            with sync_playwright() as p:
                browser_instance = p.chromium.launch(headless=True)
                page = browser_instance.new_page()
                page.goto(url)
                page.wait_for_load_state("networkidle")
                
                if selector:
                    element = page.query_selector(selector)
                    if element:
                        text = element.inner_text()
                    else:
                        text = f"Element '{selector}' not found"
                else:
                    text = page.inner_text("body")
                
                browser_instance.close()
                
                return text
        
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def click(self, url: str, selector: str, wait: int = 1000) -> str:
        """
        Click element on webpage
        
        Args:
            url: URL to interact with
            selector: CSS selector of element to click
            wait: Milliseconds to wait after click
        
        Returns:
            Success message
        """
        self._ensure_playwright()
        
        from playwright.sync_api import sync_playwright
        
        try:
            with sync_playwright() as p:
                browser_instance = p.chromium.launch(headless=True)
                page = browser_instance.new_page()
                page.goto(url)
                page.wait_for_load_state("networkidle")
                
                page.click(selector)
                page.wait_for_timeout(wait)
                
                new_url = page.url
                
                browser_instance.close()
                
                return f"Clicked {selector}. New URL: {new_url}"
        
        except Exception as e:
            return f"Error clicking element: {str(e)}"
    
    def fill(self, url: str, selector: str, value: str) -> str:
        """
        Fill input field on webpage
        
        Args:
            url: URL to interact with
            selector: CSS selector of input field
            value: Value to fill
        
        Returns:
            Success message
        """
        self._ensure_playwright()
        
        from playwright.sync_api import sync_playwright
        
        try:
            with sync_playwright() as p:
                browser_instance = p.chromium.launch(headless=True)
                page = browser_instance.new_page()
                page.goto(url)
                page.wait_for_load_state("networkidle")
                
                page.fill(selector, value)
                
                browser_instance.close()
                
                return f"Filled {selector} with '{value}'"
        
        except Exception as e:
            return f"Error filling field: {str(e)}"
    
    def search(self, query: str, engine: str = "google") -> str:
        """
        Search on search engine and return results
        
        Args:
            query: Search query
            engine: Search engine (google, duckduckgo, bing)
        
        Returns:
            Search results summary
        """
        self._ensure_playwright()
        
        from playwright.sync_api import sync_playwright
        
        # Search engine URLs
        search_urls = {
            "google": f"https://www.google.com/search?q={query.replace(' ', '+')}",
            "duckduckgo": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
            "bing": f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        }
        
        if engine not in search_urls:
            return f"Error: Unknown search engine '{engine}'"
        
        try:
            with sync_playwright() as p:
                browser_instance = p.chromium.launch(headless=True)
                page = browser_instance.new_page()
                page.goto(search_urls[engine])
                page.wait_for_load_state("networkidle")
                
                # Extract search results (engine-specific selectors)
                results = []
                if engine == "google":
                    elements = page.query_selector_all(".g")
                    for elem in elements[:5]:  # Top 5 results
                        title_elem = elem.query_selector("h3")
                        if title_elem:
                            results.append(title_elem.inner_text())
                
                elif engine == "duckduckgo":
                    elements = page.query_selector_all(".result__title")
                    for elem in elements[:5]:
                        results.append(elem.inner_text())
                
                browser_instance.close()
                
                if results:
                    return f"Top {len(results)} results for '{query}':\n" + "\n".join([f"{i+1}. {r}" for i, r in enumerate(results)])
                else:
                    return f"No results found for '{query}'"
        
        except Exception as e:
            return f"Error searching: {str(e)}"
    
    def download(self, url: str, output_dir: str = "~/Downloads") -> str:
        """
        Download file from URL
        
        Args:
            url: URL to download
            output_dir: Directory to save file
        
        Returns:
            Path to downloaded file
        """
        self._ensure_playwright()
        
        from playwright.sync_api import sync_playwright
        import os
        
        output_dir = os.path.expanduser(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            with sync_playwright() as p:
                browser_instance = p.chromium.launch(headless=True)
                page = browser_instance.new_page()
                
                # Set download directory
                page.context.set_default_timeout(60000)  # 60s timeout
                
                # Start download
                with page.expect_download() as download_info:
                    page.goto(url)
                
                download = download_info.value
                file_path = os.path.join(output_dir, download.suggested_filename)
                download.save_as(file_path)
                
                browser_instance.close()
                
                return f"Downloaded to {file_path}"
        
        except Exception as e:
            return f"Error downloading: {str(e)}"
