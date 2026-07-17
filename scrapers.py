
import asyncio
from playwright.async_api import async_playwright
import re
import requests
import base64
from typing import Dict, List, Optional
import time

class OmniScraper:
    def __init__(self):
        self.timeout = 30000 # Reduced timeout for speed
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.sources = {
            "wecima": "https://wecima.gold",
            "egybest": "https://egybest.to",
            "arabseed": "https://arabseed.show",
            "animelek": "https://animelek.me"
        }

    async def resolve_tmdb(self, tmdb_id: str, media_type: str = "movie") -> Dict:
        metadata = await self._get_metadata(tmdb_id, media_type)
        if not metadata: return {"error": "Metadata failed"}
        
        title = metadata["title"]
        year = metadata.get("year", "")
        
        # 1. Fast-track English Source (No browser needed)
        streams = []
        vidsrc_url = f"https://vidsrc.me/embed/{tmdb_id}"
        streams.append({"url": vidsrc_url, "quality": "Multi", "source": "vidsrc"})

        # 2. Sequential search for Arabic sources to save memory and avoid 502
        for name, domain in self.sources.items():
            res = await self.search_and_extract(name, domain, title, year)
            if res and res.get("streams"):
                streams.extend(res["streams"])
                break # Stop after finding first working Arabic source for speed
        
        return {"streams": streams, "metadata": metadata}

    async def search_and_extract(self, source_name: str, domain: str, title: str, year: str) -> Dict:
        async with async_playwright() as p:
            # Optimized launch for Render
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'])
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            assets = {"streams": []}
            
            try:
                query = f"{title} {year}".strip()
                search_url = f"{domain}/search/{query.replace(' ', '+')}"
                if source_name == "egybest": search_url = f"{domain}/explore/?q={query.replace(' ', '+')}"
                
                await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout)
                
                # Fast search result selection
                link = await page.eval_on_selector("a[href*='movie'], a[href*='series'], a[href*='anime']", "el => el.href")
                if not link: return {}

                # Extraction
                await page.goto(link, wait_until="domcontentloaded", timeout=self.timeout)
                if "wecima" in link:
                    content = await page.content()
                    match = re.search(r'mycimafsd=([^"]+)', content)
                    if match:
                        encoded = match.group(1)
                        missing_padding = len(encoded) % 4
                        if missing_padding: encoded += '=' * (4 - missing_padding)
                        provider_url = base64.b64decode(encoded).decode('utf-8')
                        await page.goto(provider_url, wait_until="networkidle", timeout=self.timeout)
                        await page.click("button.play, .vjs-big-play-button", timeout=5000)
                        await asyncio.sleep(3)
                else:
                    await asyncio.sleep(5)

                # Intercept M3U8 links from network
                # (Actual interception would happen via page.on("request") in a more robust way)
                return assets
            except: return {}
            finally: await browser.close()

    async def _get_metadata(self, tmdb_id: str, media_type: str) -> Optional[Dict]:
        # Fast metadata fetch via API
        try:
            url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key=4f298c2054673003f848556c2307c71f"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return {"title": data.get("title") or data.get("name"), "year": (data.get("release_date") or data.get("first_air_date", ""))[:4]}
        except: pass
        return None
