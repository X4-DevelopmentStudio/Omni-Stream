
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from scrapers import OmniScraper
import uvicorn
import os
from datetime import datetime
import asyncio

app = FastAPI(
    title="Omni-Stream API Service", 
    version="5.0.0",
    description="Automated M3U8 Extraction Service for Apps"
)

# Enable CORS for all origins (Required for app integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = OmniScraper()
cache = {}

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Omni-Stream API Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #0a0a0a; color: #eee; padding: 40px; text-align: center; }
            .card { background: #111; padding: 30px; border-radius: 12px; border: 1px solid #333; max-width: 600px; margin: auto; }
            h1 { color: #00d2ff; }
            .status { color: #00ff88; font-weight: bold; }
            code { background: #222; padding: 5px 10px; border-radius: 4px; color: #ffcc00; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 Omni-Stream API Service</h1>
            <p>Status: <span class="status">ONLINE</span></p>
            <p>Your app can now call this API directly.</p>
            <hr style="border: 0.5px solid #333;">
            <p>Endpoint: <code>/extract?url=TARGET_URL</code></p>
        </div>
    </body>
    </html>
    """

@app.get("/extract")
async def extract(
    url: str = Query(..., description="The movie/series page URL to extract from"),
    bypass_cache: bool = Query(False)
):
    # Check Cache
    if not bypass_cache and url in cache:
        if (datetime.now() - cache[url]['time']).seconds < 3600:
            return cache[url]['data']

    try:
        # Perform extraction
        result = await scraper.extract_god_mode(url)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Format a clean response for apps
        response_data = {
            "success": True,
            "url": url,
            "metadata": result.get("metadata", {}),
            "streams": result.get("streams", []),
            "subtitles": result.get("subtitles", []),
            "headers": {
                "User-Agent": scraper.user_agent,
                "Referer": url
            },
            "timestamp": datetime.now().isoformat()
        }
        
        cache[url] = {"time": datetime.now(), "data": response_data}
        return response_data
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)
