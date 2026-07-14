
import asyncio
from playwright.async_api import async_playwright
import re
import requests
import base64
from typing import Dict, List, Optional
import time

class OmniScraper:
    def __init__(self):
        self.timeout = 60000
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    async def extract_god_mode(self, url: str) -> Dict:
        # Special handling for WeCima/MyCima as they use base64 encoded player URLs
        if "wecima" in url or "mycima" in url:
            return await self.extract_wecima(url)
        
        return await self.generic_extract(url)

    async def extract_wecima(self, url: str) -> Dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            
            assets = {"streams": [], "subtitles": [], "metadata": {}}
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                assets["metadata"]["title"] = await page.title()
                
                # WeCima specific: find the iframe that contains the player
                # It usually has a src like https://akhbarworld.online/?mycimafsd=...
                content = await page.content()
                match = re.search(r'src="([^"]*akhbarworld\.online[^"]*mycimafsd=([^"]+))"', content)
                
                if match:
                    player_url = match.group(1)
                    encoded_data = match.group(2)
                    
                    # Decode the actual stream provider URL
                    try:
                        missing_padding = len(encoded_data) % 4
                        if missing_padding:
                            encoded_data += '=' * (4 - missing_padding)
                        decoded_provider = base64.b64decode(encoded_data).decode('utf-8')
                        
                        # Now navigate to the provider URL to get the actual M3U8
                        print(f"Navigating to provider: {decoded_provider}")
                        provider_page = await context.new_page()
                        
                        # Listen for M3U8 on the provider page
                        provider_page.on("request", lambda req: self._intercept(req, assets))
                        
                        await provider_page.goto(decoded_provider, wait_until="networkidle", timeout=self.timeout)
                        
                        # Try to click play on the provider page
                        play_btn = await provider_page.query_selector("button.play, .vjs-big-play-button")
                        if play_btn:
                            await play_btn.click()
                            await asyncio.sleep(5)
                            
                        await provider_page.close()
                    except Exception as e:
                        print(f"Provider extraction failed: {e}")
                
                # If still no streams, try generic on the main page
                if not assets["streams"]:
                    page.on("request", lambda req: self._intercept(req, assets))
                    await asyncio.sleep(5)

                return assets
            except Exception as e:
                return {"error": str(e)}
            finally:
                await browser.close()

    async def generic_extract(self, url: str) -> Dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            assets = {"streams": [], "subtitles": [], "metadata": {}}
            page.on("request", lambda req: self._intercept(req, assets))
            try:
                await page.goto(url, wait_until="networkidle", timeout=self.timeout)
                assets["metadata"]["title"] = await page.title()
                await asyncio.sleep(10)
                return assets
            except Exception as e:
                return {"error": str(e)}
            finally:
                await browser.close()

    def _intercept(self, request, assets):
        url = request.url
        if ".m3u8" in url:
            if url not in [s['url'] for s in assets["streams"]]:
                assets["streams"].append({"url": url, "type": "hls"})
        elif any(ext in url.lower() for ext in [".vtt", ".srt", "subtitle"]):
            if url not in [sub['url'] for sub in assets["subtitles"]]:
                assets["subtitles"].append({"url": url, "type": "subtitle"})
