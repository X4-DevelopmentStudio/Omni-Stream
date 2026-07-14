
import asyncio
from playwright.async_api import async_playwright
import re
import requests
from typing import Dict, List, Optional
import time
import random

class OmniScraper:
    def __init__(self):
        self.timeout = 50000
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    def get_random_ua(self):
        return random.choice(self.user_agents)

    def validate_link(self, url: str, headers: Dict) -> bool:
        try:
            response = requests.head(url, timeout=5, headers=headers)
            return response.status_code < 400
        except:
            return False

    async def extract_enterprise(self, url: str) -> Dict:
        ua = self.get_random_ua()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=ua)
            page = await context.new_page()
            
            streams = []
            subtitles = []
            metadata = {"title": "Unknown", "poster": None, "description": None}
            playback_headers = {"User-Agent": ua, "Referer": url}

            # Intercept network requests
            async def intercept_request(request):
                # Capture M3U8 Streams
                if ".m3u8" in request.url:
                    if request.url not in [s['url'] for s in streams]:
                        streams.append({
                            "type": "hls",
                            "url": request.url,
                            "headers": {**request.headers, "Referer": url}
                        })
                
                # Capture Subtitles (VTT/SRT)
                if any(ext in request.url for ext in [".vtt", ".srt", "subtitle"]):
                    if request.url not in [sub['url'] for sub in subtitles]:
                        lang = "Unknown"
                        # Simple language detection from URL
                        for l in ['ar', 'en', 'fr', 'es']:
                            if f"_{l}" in request.url.lower() or f"-{l}" in request.url.lower():
                                lang = l.upper()
                        subtitles.append({
                            "language": lang,
                            "url": request.url,
                            "format": "VTT" if ".vtt" in request.url else "SRT"
                        })

            page.on("request", intercept_request)
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                
                # Enhanced Metadata Extraction
                metadata["title"] = await page.title()
                try:
                    metadata["poster"] = await page.eval_on_selector("meta[property='og:image']", "el => el.content")
                    metadata["description"] = await page.eval_on_selector("meta[name='description']", "el => el.content")
                except: pass

                # Trigger Players
                selectors = ["button.play", "div.play-button", ".vjs-big-play-button", ".play-btn", "#play-video"]
                for selector in selectors:
                    try:
                        btn = await page.wait_for_selector(selector, timeout=2000)
                        if btn: await btn.click(); await asyncio.sleep(3)
                    except: continue

                # Deep scan iframes
                for frame in page.frames:
                    try:
                        for selector in selectors:
                            btn = await frame.query_selector(selector)
                            if btn: await btn.click(); await asyncio.sleep(2)
                    except: continue

                await asyncio.sleep(5)

                return {
                    "metadata": metadata,
                    "streams": streams,
                    "subtitles": subtitles,
                    "playback_requirements": {
                        "headers": playback_headers,
                        "note": "Use these headers in your player to bypass hotlink protection."
                    },
                    "status": "success",
                    "timestamp": time.time()
                }
            
            except Exception as e:
                return {"error": str(e)}
            finally:
                await browser.close()
