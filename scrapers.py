
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
        self.sources = {
            "wecima": "https://wecima.gold",
            "egybest": "https://egybest.to",
            "arabseed": "https://arabseed.show",
            "animelek": "https://animelek.me",
            "vidsrc": "https://vidsrc.me/embed/" # English source
        }

    async def resolve_tmdb(self, tmdb_id: str, media_type: str = "movie") -> Dict:
        metadata = await self._get_metadata(tmdb_id, media_type)
        if not metadata or not metadata.get("title"):
            return {"error": f"Could not resolve TMDB ID {tmdb_id}"}

        title = metadata["title"]
        year = metadata.get("year", "")
        print(f"Resolved: {title} ({year})")
        
        # Parallel search across diverse sources
        tasks = [self.search_and_extract(name, domain, title, year, tmdb_id) for name, domain in self.sources.items()]
        results = await asyncio.gather(*tasks)
        
        final_assets = {"streams": [], "subtitles": [], "metadata": metadata}
        for res in results:
            if res:
                final_assets["streams"].extend(res.get("streams", []))
                final_assets["subtitles"].extend(res.get("subtitles", []))
        
        return final_assets

    async def search_and_extract(self, source_name: str, domain: str, title: str, year: str, tmdb_id: str) -> Dict:
        # Special handling for vidsrc (English)
        if source_name == "vidsrc":
            return await self._extract_vidsrc(tmdb_id)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            try:
                # Search Logic
                query = f"{title} {year}".strip()
                if source_name == "wecima": search_url = f"{domain}/search/{query.replace(' ', '+')}"
                elif source_name == "egybest": search_url = f"{domain}/explore/?q={query.replace(' ', '+')}"
                elif source_name == "animelek": search_url = f"{domain}/search?q={query.replace(' ', '+')}"
                else: search_url = f"{domain}/?s={query.replace(' ', '+')}"
                
                await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout)
                
                # Result selection with year validation
                selectors = [".grid-item a", ".movie-item a", "a[title*='" + title[:4] + "']", "h3 a"]
                target_link = None
                for selector in selectors:
                    elements = await page.query_selector_all(selector)
                    for el in elements:
                        text = await el.inner_text()
                        href = await el.get_attribute("href")
                        if href and (title.lower() in text.lower() or year in text):
                            target_link = href
                            break
                    if target_link: break
                
                if not target_link: return {}
                return await self._extract_from_page(context, target_link)
            except: return {}
            finally: await browser.close()

    async def _extract_vidsrc(self, tmdb_id: str) -> Dict:
        # Vidsrc is a direct embed for TMDB IDs
        url = f"https://vidsrc.me/embed/{tmdb_id}"
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            assets = {"streams": [], "subtitles": []}
            page.on("request", lambda r: assets["streams"].append({"url": r.url, "type": "hls"}) if ".m3u8" in r.url else None)
            try:
                await page.goto(url, wait_until="networkidle", timeout=self.timeout)
                await asyncio.sleep(5)
                return assets
            except: return {}
            finally: await browser.close()

    async def _extract_from_page(self, context, url: str) -> Dict:
        page = await context.new_page()
        assets = {"streams": [], "subtitles": []}
        async def intercept(req):
            if ".m3u8" in req.url:
                assets["streams"].append({"url": req.url, "type": "hls"})
            if any(ext in req.url for ext in [".vtt", ".srt"]):
                assets["subtitles"].append({"url": req.url, "type": "subtitle"})
        page.on("request", intercept)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
            if "wecima" in url:
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
        finally: await page.close()

    async def _get_metadata(self, tmdb_id: str, media_type: str) -> Optional[Dict]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(f"https://www.themoviedb.org/{media_type}/{tmdb_id}", timeout=self.timeout)
                raw_title = await page.title()
                # Extract title and year: "Fight Club (1999) — The Movie Database"
                match = re.search(r'(.*?) \((.*?)\)', raw_title)
                if match:
                    return {"title": match.group(1).strip(), "year": match.group(2).strip()}
                return {"title": raw_title.split('—')[0].strip()}
            except: return None
            finally: await browser.close()
