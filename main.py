
from fastapi import FastAPI, HTTPException
from typing import Optional
from scrapers import OmniScraper
import uvicorn
import os
import asyncio

app = FastAPI(title="Omni-Stream API", description="Professional M3U8 Link Extractor")
scraper = OmniScraper()

@app.get("/")
async def read_root():
    return {"message": "Welcome to Omni-Stream Professional API! Use /extract to get M3U8 links."}

@app.get("/extract")
async def extract_m3u8_link(
    site: str,
    url: str
):
    # The scraper now handles the extraction using Playwright
    # We use asyncio to run the extraction without blocking the main thread
    try:
        result = await scraper.extract_m3u8(url)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)
