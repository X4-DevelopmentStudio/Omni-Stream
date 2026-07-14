
import asyncio
from playwright.async_api import async_playwright
import re
import requests
from typing import Dict, List, Optional
import time
import random

class OmniScraper:
    def __init__(self):
        self.timeout = 60000 # 60 seconds for God Mode
        self.profiles = [
            {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "viewport": {"width": 1920, "height": 1080}},
            {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.0 Safari/537.36", "viewport": {"width": 1440, "height": 900}},
            {"ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", "viewport": {"width": 390, "height": 844}}
        ]

    async def extract_god_mode(self, url: str, retries: int = 2) -> Dict:
        for attempt in range(retries + 1):
            profile = random.choice(self.profiles)
            result = await self._perform_extraction(url, profile)
            if "streams" in result and result["streams"]:
                return result
            if attempt < retries:
                await asyncio.sleep(2) # Wait before retry
        return {"error": "All extraction attempts failed. The site might be using advanced protection.", "status": "failed"}

    async def _perform_extraction(self, url: str, profile: Dict) -> Dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=profile["ua"], viewport=profile["viewport"])
            page = await context.new_page()
            
            assets = {"streams": [], "subtitles": [], "metadata": {}}
            
            async def handle_request(request):
                # Intercept M3U8
                if ".m3u8" in request.url:
                    if request.url not in [s['url'] for s in assets["streams"]]:
                        assets["streams"].append({"url": request.url, "headers": request.headers})
                
                # Intercept Subtitles
                if any(ext in request.url.lower() for ext in [".vtt", ".srt", "subtitle"]):
                    if request.url not in [sub['url'] for sub in assets["subtitles"]]:
                        assets["subtitles"].append({"url": request.url, "type": "subtitle"})

            page.on("request", handle_request)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=self.timeout)
                
                # Metadata
                assets["metadata"]["title"] = await page.title()
                try:
                    assets["metadata"]["poster"] = await page.eval_on_selector("meta[property='og:image']", "el => el.content")
                except: pass

                # Recursive Iframe Interaction
                async def interact_with_frames(frames):
                    for frame in frames:
                        try:
                            # Try to click common play buttons
                            buttons = await frame.query_selector_all("button, div, i, svg")
                            for btn in buttons:
                                try:
                                    # Click if it looks like a play button
                                    html = await btn.inner_html()
                                    if any(x in html.lower() for x in ['play', 'start', 'video', 'fa-play']):
                                        await btn.click(timeout=1000)
                                        await asyncio.sleep(1)
                                except: continue
                            
                            # Recurse into child frames
                            if frame.child_frames:
                                await interact_with_frames(frame.child_frames)
                        except: continue

                await interact_with_frames(page.frames)
                await asyncio.sleep(5) # Final wait for network

                return assets
            except Exception as e:
                return {"error": str(e)}
            finally:
                await browser.close()
