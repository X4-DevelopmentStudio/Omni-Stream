
import asyncio
from playwright.async_api import async_playwright
import re
from typing import Dict, Optional

class OmniScraper:
    def __init__(self):
        self.timeout = 30000  # 30 seconds

    async def extract_m3u8(self, url: str) -> Dict:
        """
        Uses Playwright to navigate to a page and intercept network requests
        to find the final M3U8 streaming link.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Create a context with a realistic user agent
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            m3u8_link = None
            
            # Intercept network requests
            async def intercept_request(request):
                nonlocal m3u8_link
                if ".m3u8" in request.url:
                    m3u8_link = request.url

            page.on("request", intercept_request)
            
            try:
                # Navigate to the URL
                await page.goto(url, wait_until="networkidle", timeout=self.timeout)
                
                # Some sites require clicking a play button to trigger the M3U8 load
                # We'll try to find and click common play button patterns
                play_buttons = [
                    "button.play", "div.play-button", ".vjs-big-play-button", 
                    "i.fa-play", "svg.play-icon"
                ]
                for selector in play_buttons:
                    try:
                        if await page.is_visible(selector):
                            await page.click(selector)
                            await asyncio.sleep(2) # Wait for potential load
                    except:
                        continue

                # Wait a bit more for any dynamic loads
                if not m3u8_link:
                    await asyncio.sleep(5)

                if m3u8_link:
                    return {
                        "url": url,
                        "m3u8_link": m3u8_link,
                        "status": "success"
                    }
                else:
                    return {"error": "Could not capture M3U8 link via network interception"}
            
            except Exception as e:
                return {"error": f"Extraction failed: {str(e)}"}
            finally:
                await browser.close()

    def extract(self, site: str, url: str) -> Dict:
        # Since the extraction is now async, we'll run it in the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.extract_m3u8(url))
        finally:
            loop.close()

