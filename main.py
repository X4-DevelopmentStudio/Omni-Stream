
from fastapi import FastAPI, HTTPException
from typing import Optional

app = FastAPI(title="Omni-Stream API", description="API for extracting M3U8 video links from various streaming sites.")

@app.get("/")
async def read_root():
    return {"message": "Welcome to Omni-Stream API! Use /extract to get M3U8 links."}

@app.get("/extract")
async def extract_m3u8_link(
    site: str,
    url: str,
    quality: Optional[str] = None
):
    # Placeholder for extraction logic
    # In a real scenario, this would call a scraper function based on the 'site' parameter
    if site.lower() == "egybest":
        # Simulate extraction for EgyBest
        if "example.com/egybest/movie123" in url:
            return {"site": site, "url": url, "m3u8_link": "https://example.com/egybest/movie123/stream.m3u8", "quality": quality or "auto"}
        else:
            raise HTTPException(status_code=404, detail="Movie not found on EgyBest (simulated)")
    elif site.lower() == "mycima":
        # Simulate extraction for MyCima
        if "example.com/mycima/series456" in url:
            return {"site": site, "url": url, "m3u8_link": "https://example.com/mycima/series456/stream.m3u8", "quality": quality or "auto"}
        else:
            raise HTTPException(status_code=404, detail="Series not found on MyCima (simulated)")
    else:
        raise HTTPException(status_code=400, detail=f"Extraction for site '{site}' is not yet supported.")

