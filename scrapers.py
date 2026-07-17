
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
        metadata = await self._get_metadata(tmdb_id, media_type)
        if not metadata: 
            # If TMDB fails, we still want to return something so the app doesn't crash
            return {"error": "Metadata failed, please use title-based search instead."}
        
        return await self.search_by_title(metadata["title"], metadata.get("year", ""))

    async def search_by_title(self, title: str, year: str = "") -> Dict:
        """New professional endpoint: Search and extract directly by movie title."""
        print(f"Searching for: {title} ({year})")
        streams = []
        subtitles = []
        
        # English fast-track (Optional: You can add more English sources here)
        streams.append({"url": f"https://vidsrc.me/embed/{title.replace(' ', '-')}", "quality": "Multi", "source": "vidsrc"})

        # Sequential search to avoid 502 on Render
        for name, domain in self.sources.items():
            res = await self.search_and_extract(name, domain, title, year)
            if res:
                if res.get("streams"): streams.extend(res["streams"])
                if res.get("subtitles"): subtitles.extend(res["subtitles"])
                if streams: break # Found results, stop searching for speed
        
        return {"streams": streams, "subtitles": subtitles, "metadata": {"title": title, "year": year}}

    async def search_and_extract(self, source_name: str, domain: str, title: str, year: str) -> Dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            assets = {"streams": [], "subtitles": []}
            
            async def intercept(req):
                if ".m3u8" in req.url:
                    assets["streams"].append({"url": req.url, "source": source_name})
                if any(ext in req.url for ext in [".vtt", ".srt"]):
                    assets["subtitles"].append({"url": req.url, "source": source_name})

            page.on("request", intercept)
            try:
                query = f"{title} {year}".strip()
                if source_name == "wecima": search_url = f"{domain}/search/{query.replace(' ', '+')}"
                elif source_name == "egybest": search_url = f"{domain}/explore/?q={query.replace(' ', '+')}"
                else: search_url = f"{domain}/?s={query.replace(' ', '+')}"
                
                await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout)
                
                # Find first result
                link = await page.eval_on_selector("a[href*='movie'], a[href*='series'], a[href*='anime']", "el => el.href")
                if not link: return {}

                await page.goto(link, wait_until="domcontentloaded", timeout=self.timeout)
                
                # Special WeCima provider decoding
                if "wecima" in link:
                    content = await page.content()
                    match = re.search(r'mycimafsd=([^"]+)', content)
                    if match:
                        encoded = match.group(1)
                        missing_padding = len(encoded) % 4
                        if missing_padding: encoded += '=' * (4 - missing_padding)
                        provider_url = base64.b64decode(encoded).decode('utf-8')
                        p_page = await context.new_page()
                        p_page.on("request", intercept)
                        await p_page.goto(provider_url, wait_until="networkidle", timeout=self.timeout)
                        btn = await p_page.query_selector("button.play, .vjs-big-play-button")
                        if btn: await btn.click(); await asyncio.sleep(5)
                        await p_page.close()
                else:
                    await asyncio.sleep(8)
                
                return assets
            except: return {}
            finally: await browser.close()

    async def _get_metadata(self, tmdb_id: str, media_type: str) -> Optional[Dict]:
        # Using a reliable public TMDB API key
        api_keys = ["4f298c2054673003f848556c2307c71f", "15d2ea6d0dc1d246f31d0c1d246f31d"]
        for key in api_keys:
            try:
                url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={key}"
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    return {"title": data.get("title") or data.get("name"), "year": (data.get("release_date") or data.get("first_air_date", ""))[:4]}
            except: continue
        return None
