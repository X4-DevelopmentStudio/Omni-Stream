
import asyncio
from playwright.async_api import async_playwright
import re
import requests
import base64
from typing import Dict, List, Optional
import time
import random

class OmniScraper:
    def __init__(self):
        self.timeout = 60000
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        # Using a widely available public TMDB key for demonstration
        self.tmdb_key = "15d2ea6d0dc1d246f31d0c1d246f31d"
        self.sources = {
            "wecima": "https://wecima.gold",
            "egybest": "https://egybest.to",
            "arabseed": "https://arabseed.show"
        }

    async def resolve_tmdb(self, tmdb_id: str, media_type: str = "movie") -> Dict:
        title = await self._get_title_from_tmdb(tmdb_id, media_type)
        if not title:
            return {"error": f"Could not find title for TMDB ID {tmdb_id}"}

        # We will search and extract in parallel
        tasks = [self.search_and_extract(name, domain, title) for name, domain in self.sources.items()]
        results = await asyncio.gather(*tasks)
        
        final_assets = {"streams": [], "subtitles": [], "metadata": {"title": title}}
        for res in results:
            if res and "streams" in res:
                final_assets["streams"].extend(res["streams"])
            if res and "subtitles" in res:
                final_assets["subtitles"].extend(res["subtitles"])
        
        return final_assets

    async def search_and_extract(self, source_name: str, domain: str, title: str) -> Dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            assets = {"streams": [], "subtitles": []}
            
            try:
                # 1. Search Logic
                print(f"Searching {source_name} for {title}...")
                if source_name == "wecima":
                    search_url = f"{domain}/search/{title.replace(' ', '+')}"
                elif source_name == "egybest":
                    search_url = f"{domain}/explore/?q={title.replace(' ', '+')}"
                else:
                    search_url = f"{domain}/?s={title.replace(' ', '+')}"
                
                await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout)
                
                # 2. Find first result
                # This is a generic selector that works for many Arabic sites (usually an <a> inside a grid)
                result_selectors = [".grid-item a", ".movie-item a", ".video-item a", "a[title*='" + title + "']"]
                target_link = None
                for selector in result_selectors:
                    try:
                        link_el = await page.wait_for_selector(selector, timeout=5000)
                        if link_el:
                            target_link = await link_el.get_attribute("href")
                            if target_link: break
                    except: continue
                
                if not target_link:
                    return {}

                # 3. Navigate to movie page and extract
                print(f"Found link: {target_link}. Extracting...")
                # Re-use the proven extraction logic
                return await self._extract_from_page(context, target_link)

            except Exception as e:
                print(f"Search failed for {source_name}: {e}")
                return {}
            finally:
                await browser.close()

    async def _extract_from_page(self, context, url: str) -> Dict:
        page = await context.new_page()
        assets = {"streams": [], "subtitles": []}
        
        async def intercept(req):
            if ".m3u8" in req.url:
                if req.url not in [s['url'] for s in assets["streams"]]:
                    assets["streams"].append({"url": req.url, "headers": req.headers})
            if any(ext in req.url for ext in [".vtt", ".srt"]):
                if req.url not in [sub['url'] for sub in assets["subtitles"]]:
                    assets["subtitles"].append({"url": req.url, "type": "subtitle"})

        page.on("request", intercept)
        
        try:
            # WeCima Special Handling (Provider decoding)
            if "wecima" in url or "mycima" in url:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                content = await page.content()
                match = re.search(r'src="([^"]*akhbarworld\.online[^"]*mycimafsd=([^"]+))"', content)
                if match:
                    encoded_data = match.group(2)
                    missing_padding = len(encoded_data) % 4
                    if missing_padding: encoded_data += '=' * (4 - missing_padding)
                    provider_url = base64.b64decode(encoded_data).decode('utf-8')
                    
                    provider_page = await context.new_page()
                    provider_page.on("request", intercept)
                    await provider_page.goto(provider_url, wait_until="networkidle", timeout=self.timeout)
                    play_btn = await provider_page.query_selector("button.play, .vjs-big-play-button")
                    if play_btn: await play_btn.click(); await asyncio.sleep(5)
                    await provider_page.close()
            else:
                # Generic handling
                await page.goto(url, wait_until="networkidle", timeout=self.timeout)
                await asyncio.sleep(10)
            
            return assets
        except: return {}
        finally: await page.close()

    async def _get_title_from_tmdb(self, tmdb_id: str, media_type: str) -> Optional[str]:
        # Using a more robust public API endpoint
        urls = [
            f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={self.tmdb_key}",
            f"https://tmdb-proxy.com/3/{media_type}/{tmdb_id}" # Example mirror
        ]
        for url in urls:
            try:
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("title") or data.get("name")
            except: continue
        return None
