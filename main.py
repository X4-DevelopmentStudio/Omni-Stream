
from fastapi import FastAPI, HTTPException, Query
from scrapers import OmniScraper
import uvicorn
import os
from datetime import datetime

app = FastAPI(
    title="Omni-Stream Enterprise API", 
    description="The ultimate Arabic streaming toolkit: Video, Subtitles, Metadata, and Playback Headers.",
    version="3.0.0"
)
scraper = OmniScraper()
cache = {}

@app.get("/")
async def read_root():
    return {
        "project": "Omni-Stream Enterprise",
        "version": "3.0.0",
        "status": "Online",
        "capabilities": [
            "Multi-Source M3U8 Extraction",
            "Subtitle Discovery (VTT/SRT)",
            "Dynamic Metadata Enrichment",
            "Anti-Hotlink Header Generation",
            "User-Agent Rotation"
        ]
    }

@app.get("/extract")
async def extract(
    url: str = Query(..., description="Target streaming page URL"),
    bypass_cache: bool = Query(False)
):
    if not bypass_cache and url in cache:
        if (datetime.now() - cache[url]['time']).seconds < 3600:
            return cache[url]['data']

    try:
        result = await scraper.extract_enterprise(url)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        cache[url] = {"time": datetime.now(), "data": result}
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)
