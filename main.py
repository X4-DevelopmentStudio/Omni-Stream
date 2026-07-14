
from fastapi import FastAPI, HTTPException
from typing import Optional
from scrapers import OmniScraper

app = FastAPI(title="Omni-Stream API", description="API for extracting M3U8 video links from various streaming sites.")
scraper = OmniScraper()

@app.get("/")
async def read_root():
    return {"message": "Welcome to Omni-Stream API! Use /extract to get M3U8 links."}

@app.get("/extract")
async def extract_m3u8_link(
    site: str,
    url: str
):
    result = scraper.extract(site, url)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
