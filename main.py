
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
    title="Omni-Stream Legendary Service", 
    version="7.0.0",
    description="Universal TMDB Resolver & Legendary Extraction Engine"
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

@app.get("/")
async def legendary_dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Omni-Stream Legendary</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: radial-gradient(circle, #1a1a1a, #000); color: #fff; padding: 50px; text-align: center; }
            .hero { padding: 40px; border: 2px solid #00d2ff; border-radius: 20px; display: inline-block; background: rgba(0,0,0,0.8); box-shadow: 0 0 50px #00d2ff; }
            h1 { font-size: 3em; margin: 0; color: #00d2ff; text-transform: uppercase; letter-spacing: 5px; }
            .badge { background: #00d2ff; color: #000; padding: 5px 15px; border-radius: 50px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="hero">
            <h1>Omni-Stream</h1>
            <p><span class="badge">LEGENDARY EDITION</span></p>
            <p>Universal TMDB Resolver & Auto-Recovery Active</p>
            <hr style="border: 0.5px solid #333;">
            <p>API: <code>/resolve?tmdb_id=ID&type=movie</code></p>
        </div>
    </body>
    </html>
    """

@app.get("/proxy")
async def proxy_stream(url: str, referer: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": referer,
        "Origin": referer.rstrip('/')
    }
    try:
        session = requests.Session()
        def generate():
            with session.get(url, headers=headers, stream=True, timeout=15, allow_redirects=True) as r:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    yield chunk
        return StreamingResponse(generate(), media_type="application/x-mpegURL")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resolve")
async def resolve(
    tmdb_id: str = Query(..., description="The TMDB ID of the movie/show"),
    media_type: str = Query("movie", description="movie or tv"),
    request: Request = None
):
    base_url = str(request.base_url).rstrip('/')
    cache_key = f"{tmdb_id}_{media_type}"
    
    if cache_key in cache:
        if (datetime.now() - cache[cache_key]['time']).seconds < 7200: # 2 hour cache
            return cache[cache_key]['data']

    try:
        # The Resolver finds the movie across all sites automatically
        result = await scraper.resolve_tmdb(tmdb_id, media_type)
        
        # Proxy all links for 100% reliability
        for s in result.get("streams", []):
            s["proxied_url"] = f"{base_url}/proxy?url={s['url']}&referer={result['metadata'].get('title', 'stream')}"

        response = {
            "success": True,
            "tmdb_id": tmdb_id,
            "results": result,
            "timestamp": datetime.now().isoformat()
        }
        
        cache[cache_key] = {"time": datetime.now(), "data": response}
        return response
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)
