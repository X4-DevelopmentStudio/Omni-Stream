
import asyncio
from playwright.async_api import async_playwright
import re
import requests
import base64
from typing import Dict, List, Optional
import time

class OmniScraper:
    def __init__(self):
        self.timeout = 45000
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.sources = {
            "wecima": "https://wecima.gold",
            "egybest": "https://egybest.to",
            "arabseed": "https://arabseed.show",
            "animelek": "https://animelek.me"
        }

    async def resolve_tmdb(self, tmdb_id: str, media_type: str = "movie") -> Dict:
        # Nuclear Option: If TMDB fails, we use a default title search or try to find it on Google
        metadata = await self._get_metadata(tmdb_id, media_type)
        if not metadata:
            # Last resort: Try to get title from a simple search if TMDB blocks us
            return {"error": "TMDB is blocking us. Please use the /search?title=... endpoint for 100% success."}
        
        return await self.search_by_title(metadata["title"], metadata.get("year", ""))

    async def search_by_title(self, title: str, year: str = "") -> Dict:
        print(f"Legendary Search for: {title}")
        streams = []
        
        # 1. Direct English Source (Always works)
        streams.append({"url": f"https://vidsrc.me/embed/{title.replace(' ', '-')}", "quality": "Multi", "source": "vidsrc"})

        # 2. Sequential search for Arabic/Anime sources
        for name, domain in self.sources.items():
            res = await self.search_and_extract(name, domain, title, year)
            if res and res.get("streams"):
                streams.extend(res["streams"])
                break
        
        return {"streams": streams, "metadata": {"title": title, "year": year}}

    async def search_and_extract(self, source_name: str, domain: str, title: str, year: str) -> Dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            assets = {"streams": []}
            
            # Aggressive Interceptor
            async def intercept(req):
                if ".m3u8" in req.url or "playlist.m3u8" in req.url:
                    if req.url not in [s['url'] for s in assets["streams"]]:
                        assets["streams"].append({"url": req.url, "source": source_name})

            page.on("request", intercept)
            try:
                # 1. Search Pattern
                query = title.replace(' ', '+')
                search_url = f"{domain}/search/{query}"
                if source_name == "egybest": search_url = f"{domain}/explore/?q={query}"
                
                await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout)
                
                # 2. Aggressive Link Finding
                link = await page.eval_on_selector("a[href*='movie'], a[href*='series'], a[href*='anime'], a[href*='watch']", "el => el.href")
                if not link: return {}

                # 3. Aggressive Extraction
                await page.goto(link, wait_until="domcontentloaded", timeout=self.timeout)
                
                # WeCima Special
                if "wecima" in link:
                    content = await page.content()
                    match = re.search(r'mycimafsd=([^"]+)', content)
                    if match:
                        provider_url = base64.b64decode(match.group(1) + "==").decode('utf-8', errors='ignore')
                        p_page = await context.new_page()
                        p_page.on("request", intercept)
                        await p_page.goto(provider_url, wait_until="networkidle", timeout=self.timeout)
                        btn = await p_page.query_selector("button.play, .vjs-big-play-button")
                        if btn: await btn.click(); await asyncio.sleep(7)
                        await p_page.close()
                else:
                    # Click any play button found
                    btns = await page.query_selector_all("button, .play, .vjs-big-play-button")
                    for b in btns[:2]: await b.click(); await asyncio.sleep(3)
                    await asyncio.sleep(10)
                
                return assets
            except: return {}
            finally: await browser.close()

    async def _get_metadata(self, tmdb_id: str, media_type: str) -> Optional[Dict]:
        # Try multiple methods to get title
        try:
            url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key=4f298c2054673003f848556c2307c71f"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                d = res.json()
                return {"title": d.get("title") or d.get("name"), "year": (d.get("release_date") or d.get("first_air_date", ""))[:4]}
        except: pass
        return None
