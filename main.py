
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
    title="Omni-Stream Universal Service", 
    version="8.0.0",
    description="Professional Movie & Anime Extraction API"
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
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Omni-Stream Universal API</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #0a0a0a; color: #eee; padding: 50px; text-align: center; }
            .card { background: #111; padding: 30px; border-radius: 12px; border: 1px solid #333; max-width: 600px; margin: auto; }
            h1 { color: #00d2ff; }
            code { background: #222; padding: 5px 10px; border-radius: 4px; color: #ffcc00; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 Omni-Stream Universal API</h1>
            <p>Ready for app integration.</p>
            <hr style="border: 0.5px solid #333;">
            <p>Search by Title: <code>/search?title=MovieName</code></p>
            <p>Resolve by ID: <code>/resolve?tmdb_id=ID</code></p>
        </div>
    </body>
    </html>
    """

@app.get("/proxy")
async def proxy_stream(url: str, referer: str = "https://wecima.gold"):
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

@app.get("/search")
async def search_by_title(
    title: str = Query(..., description="The title of the movie/anime"),
    year: str = Query("", description="Optional release year"),
    request: Request = None
):
    base_url = str(request.base_url).rstrip('/')
    try:
        result = await scraper.search_by_title(title, year)
        
        # Proxy links for reliability
        for s in result.get("streams", []):
            s["proxied_url"] = f"{base_url}/proxy?url={s['url']}&referer={title}"
            
        return {"success": True, "results": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/resolve")
async def resolve(
    tmdb_id: str = Query(..., description="The TMDB ID"),
    media_type: str = Query("movie", description="movie or tv"),
    request: Request = None
):
    base_url = str(request.base_url).rstrip('/')
    try:
        result = await scraper.resolve_tmdb(tmdb_id, media_type)
        if "error" in result: return {"success": False, "error": result["error"]}
        
        for s in result.get("streams", []):
            s["proxied_url"] = f"{base_url}/proxy?url={s['url']}&referer={tmdb_id}"
            
        return {"success": True, "results": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)
