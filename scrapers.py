
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
            "arabseed": "https://arabseed.show"
        }

    async def resolve_tmdb(self, tmdb_id: str, media_type: str = "movie") -> Dict:
        title = await self._get_title(tmdb_id, media_type)
        if not title or len(title) > 50: # Sanity check for failed extraction
            return {"error": f"Could not resolve TMDB ID {tmdb_id}"}

        print(f"Resolved Title: {title}")
        tasks = [self.search_and_extract(name, domain, title) for name, domain in self.sources.items()]
        results = await asyncio.gather(*tasks)
        
        final_assets = {"streams": [], "subtitles": [], "metadata": {"title": title, "tmdb_id": tmdb_id}}
        for res in results:
            if res and "streams" in res: final_assets["streams"].extend(res["streams"])
            if res and "subtitles" in res: final_assets["subtitles"].extend(res["subtitles"])
        
        return final_assets

    async def search_and_extract(self, source_name: str, domain: str, title: str) -> Dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            try:
                search_url = f"{domain}/search/{title.replace(' ', '+')}"
                if source_name == "egybest": search_url = f"{domain}/explore/?q={title.replace(' ', '+')}"
                
                await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout)
                
                # Wait for result and click first one
                result_selectors = [".grid-item a", ".movie-item a", "a[title*='" + title[:4] + "']"]
                target_link = None
                for selector in result_selectors:
                    try:
                        link_el = await page.wait_for_selector(selector, timeout=3000)
                        if link_el:
                            target_link = await link_el.get_attribute("href")
                            if target_link: break
                    except: continue
                
                if not target_link: return {}
                return await self._extract_from_page(context, target_link)
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

    async def _get_title(self, tmdb_id: str, media_type: str) -> Optional[str]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                # Use a cleaner way to get title from TMDB public page
                await page.goto(f"https://www.themoviedb.org/{media_type}/{tmdb_id}", timeout=self.timeout)
                raw_title = await page.title()
                # Example: "Fight Club (1999) — The Movie Database (TMDB)"
                clean_title = raw_title.split('(')[0].split('—')[0].strip()
                return clean_title
            except: return None
            finally: await browser.close()
