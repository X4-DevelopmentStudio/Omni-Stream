
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
from scrapers import OmniScraper
import uvicorn
import os
import asyncio
from datetime import datetime

app = FastAPI(
    title="Omni-Stream Ultimate API", 
    description="The most advanced Arabic streaming link extractor with Multi-Quality, Metadata, and Validation.",
    version="2.0.0"
)
scraper = OmniScraper()

# Simple In-Memory Cache for demo (would use Redis in production)
cache = {}

@app.get("/")
async def read_root():
    return {
        "project": "Omni-Stream",
        "status": "Online",
        "features": [
            "Multi-Quality Detection",
            "Real-time Link Validation",
            "Metadata Enrichment",
            "Headless Interception",
            "Anti-Bot Bypass"
        ],
        "endpoints": {
            "/extract": "GET - Extract links with site and url params",
            "/health": "GET - System health check"
        }
    }

@app.get("/extract")
async def extract_m3u8_link(
    url: str = Query(..., description="The full URL of the movie or series page"),
    site: Optional[str] = Query(None, description="Optional site identifier"),
    bypass_cache: bool = Query(False, description="Force fresh extraction")
):
    # Check Cache
    if not bypass_cache and url in cache:
        # Check if cache is fresh (e.g., < 1 hour)
        cached_data = cache[url]
        if (datetime.now() - cached_data['time']).seconds < 3600:
            return cached_data['data']

    try:
        result = await scraper.extract_m3u8(url)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Save to Cache
        cache[url] = {
            "time": datetime.now(),
            "data": result
        }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)
