
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from scrapers import OmniScraper
import uvicorn
import os
from datetime import datetime
import asyncio

app = FastAPI(title="Omni-Stream God Mode", version="4.0.0")
scraper = OmniScraper()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Omni-Stream God Mode Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f0f0f; color: #fff; padding: 40px; }
            .container { max-width: 800px; margin: auto; background: #1a1a1a; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
            h1 { color: #00d2ff; text-align: center; }
            input { width: 100%; padding: 15px; margin: 20px 0; border-radius: 8px; border: none; background: #333; color: #fff; box-sizing: border-box; }
            button { width: 100%; padding: 15px; border-radius: 8px; border: none; background: #00d2ff; color: #000; font-weight: bold; cursor: pointer; transition: 0.3s; }
            button:hover { background: #009ec2; }
            #results { margin-top: 30px; background: #222; padding: 20px; border-radius: 8px; display: none; word-break: break-all; }
            .loader { border: 4px solid #333; border-top: 4px solid #00d2ff; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 20px auto; display: none; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Omni-Stream God Mode</h1>
            <p style="text-align:center; color:#888;">Universal Arabic Streaming Link Extractor</p>
            <input type="text" id="urlInput" placeholder="Enter movie/series URL (EgyBest, WeCima, ArabSeed, etc.)">
            <button onclick="extract()">EXTRACT REAL LINKS</button>
            <div class="loader" id="loader"></div>
            <pre id="results"></pre>
        </div>
        <script>
            async function extract() {
                const url = document.getElementById('urlInput').value;
                const results = document.getElementById('results');
                const loader = document.getElementById('loader');
                
                if(!url) return alert('Please enter a URL');
                
                results.style.display = 'none';
                loader.style.display = 'block';
                
                try {
                    const response = await fetch(`/extract?url=${encodeURIComponent(url)}`);
                    const data = await response.json();
                    results.textContent = JSON.stringify(data, null, 2);
                    results.style.display = 'block';
                } catch (e) {
                    alert('Extraction failed');
                } finally {
                    loader.style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/extract")
async def extract(url: str = Query(...)):
    try:
        result = await scraper.extract_god_mode(url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)
