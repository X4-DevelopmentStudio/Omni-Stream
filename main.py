
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
    version="6.0.0",
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
            <p>Proxy Service is ACTIVE to fix 403 errors.</p>
            <hr style="border: 0.5px solid #333;">
            <p>API Endpoint: <code>{base_url}/extract?url=TARGET_URL</code></p>
        </div>
    </body>
    </html>
    """

@app.get("/proxy")
async def proxy_stream(url: str, referer: str):
    """
    Proxies the M3U8/TS stream to bypass 403 Forbidden errors.
    """
    headers = {
        "User-Agent": scraper.user_agent,
        "Referer": referer
    }
    
    def generate():
        with requests.get(url, headers=headers, stream=True, timeout=10) as r:
            for chunk in r.iter_content(chunk_size=8192):
                yield chunk

    return StreamingResponse(generate(), media_type="application/x-mpegURL")

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
        
        # Create proxied links to ensure they work 100%
        proxied_streams = []
        for s in result.get("streams", []):
            proxied_url = f"{base_url}/proxy?url={s['url']}&referer={url}"
            proxied_streams.append({
                "quality": s.get("quality", "Auto"),
                "original_url": s['url'],
                "proxied_url": proxied_url,
                "type": "hls"
            })

        response_data = {
            "success": True,
            "url": url,
            "metadata": result.get("metadata", {}),
            "streams": proxied_streams,
            "subtitles": result.get("subtitles", []),
            "playback_headers": {
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
