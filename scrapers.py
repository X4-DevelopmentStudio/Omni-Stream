
import asyncio
from playwright.async_api import async_playwright
import re
import requests
from typing import Dict, List, Optional
import time

class OmniScraper:
    def __init__(self):
        self.timeout = 45000  # 45 seconds for heavy sites
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def validate_link(self, m3u8_url: str) -> bool:
        """Checks if the M3U8 link is actually reachable and active."""
        try:
            response = requests.head(m3u8_url, timeout=5, headers={'User-Agent': self.user_agent})
            return response.status_code < 400
        except:
            return False

    async def extract_m3u8(self, url: str) -> Dict:
        """
        Professional extraction with network interception, multi-quality detection,
        and real-time validation.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            
            streams = []
            metadata = {"title": "Unknown", "poster": None}

            # Intercept network requests for M3U8 links
            async def intercept_request(request):
                if ".m3u8" in request.url:
                    if request.url not in [s['url'] for s in streams]:
                        # Basic quality detection from URL
                        quality = "Auto"
                        if "1080" in request.url: quality = "1080p"
                        elif "720" in request.url: quality = "720p"
                        elif "480" in request.url: quality = "480p"
                        elif "360" in request.url: quality = "360p"
                        
                        streams.append({
                            "quality": quality,
                            "url": request.url,
                            "valid": self.validate_link(request.url)
                        })

            page.on("request", intercept_request)
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                
                # Extract Metadata (Professional Touch)
                try:
                    metadata["title"] = await page.title()
                    metadata["poster"] = await page.eval_on_selector("meta[property='og:image']", "el => el.content")
                except:
                    pass

                # Aggressive interaction to trigger players
                selectors = [
                    "button.play", "div.play-button", ".vjs-big-play-button", 
                    "i.fa-play", "svg.play-icon", ".play-btn", "#play-video"
                ]
                
                # Wait for any of these to be visible and click
                for selector in selectors:
                    try:
                        btn = await page.wait_for_selector(selector, timeout=2000)
                        if btn:
                            await btn.click()
                            await asyncio.sleep(3)
                    except:
                        continue

                # Handle Iframes (Deep Scan)
                iframes = page.frames
                for frame in iframes:
                    try:
                        # Try to click play inside iframes
                        for selector in selectors:
                            btn = await frame.query_selector(selector)
                            if btn:
                                await btn.click()
                                await asyncio.sleep(2)
                    except:
                        continue

                # Final wait for dynamic loading
                await asyncio.sleep(5)

                if streams:
                    # Sort streams by quality if possible
                    return {
                        "metadata": metadata,
                        "streams": streams,
                        "status": "success",
                        "timestamp": time.time()
                    }
                else:
                    return {"error": "No active M3U8 streams captured. The site might have advanced anti-bot protection."}
            
            except Exception as e:
                return {"error": f"Extraction failed: {str(e)}"}
            finally:
                await browser.close()
