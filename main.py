
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from scrapers import OmniScraper
import uvicorn
import os
from datetime import datetime
import asyncio
import requests

app = FastAPI(
    title="Omni-Stream Pro Service", 
    version="6.1.0",
    description="Automated M3U8 Extraction & Proxy Service"
)

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
async def dashboard(request: Request):
    base_url = str(request.base_url).rstrip('/')
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Omni-Stream Pro Dashboard</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #0a0a0a; color: #eee; padding: 40px; text-align: center; }}
            .card {{ background: #111; padding: 30px; border-radius: 12px; border: 1px solid #333; max-width: 600px; margin: auto; }}
            h1 {{ color: #00d2ff; }}
            .status {{ color: #00ff88; font-weight: bold; }}
            code {{ background: #222; padding: 5px 10px; border-radius: 4px; color: #ffcc00; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 Omni-Stream Pro Service</h1>
            <p>Status: <span class="status">ONLINE</span></p>
            <p>Advanced Proxying is ACTIVE.</p>
            <hr style="border: 0.5px solid #333;">
            <p>API Endpoint: <code>{base_url}/extract?url=TARGET_URL</code></p>
        </div>
    </body>
    </html>
    """

@app.get("/proxy")
async def proxy_stream(url: str, referer: str):
    """
    Proxies the M3U8/TS stream with full header injection.
    """
    # We use the original referer and a modern UA to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": referer,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": referer.rstrip('/')
    }
    
    try:
        # We use a session to handle any cookies if needed
        session = requests.Session()
        def generate():
            with session.get(url, headers=headers, stream=True, timeout=15, allow_redirects=True) as r:
                for chunk in r.iter_content(chunk_size=1024*1024): # 1MB chunks
                    yield chunk

        return StreamingResponse(generate(), media_type="application/x-mpegURL")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/extract")
async def extract(
    request: Request,
    url: str = Query(..., description="The movie/series page URL"),
    bypass_cache: bool = Query(False)
):
    base_url = str(request.base_url).rstrip('/')
    
    if not bypass_cache and url in cache:
        if (datetime.now() - cache[url]['time']).seconds < 3600:
            return cache[url]['data']

    try:
        result = await scraper.extract_god_mode(url)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Create proxied links
        proxied_streams = []
        for s in result.get("streams", []):
            # We pass the provider URL as the referer if available, else the main URL
            actual_referer = s.get("headers", {}).get("referer", url)
            proxied_url = f"{base_url}/proxy?url={s['url']}&referer={actual_referer}"
            
            # Simple quality detection
            quality = "Auto"
            if "1080" in s['url']: quality = "1080p"
            elif "720" in s['url']: quality = "720p"
            elif "480" in s['url']: quality = "480p"

            proxied_streams.append({
                "quality": quality,
                "url": proxied_url,
                "original_url": s['url'],
                "type": "hls"
            })

        response_data = {
            "success": True,
            "metadata": result.get("metadata", {}),
            "streams": proxied_streams,
            "subtitles": result.get("subtitles", []),
            "timestamp": datetime.now().isoformat()
        }
        
        cache[url] = {"time": datetime.now(), "data": response_data}
        return response_data
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)
