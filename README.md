# 🚀 Omni-Stream Ultimate

**Omni-Stream** is the most advanced, professional-grade Arabic streaming link extractor available on GitHub. It uses high-end headless browsing and network interception technology to capture real-world M3U8 streaming links from virtually any Arabic platform.

## 🌟 Advanced Features
- **🎯 Multi-Quality Extraction**: Automatically detects and categorizes streams by quality (1080p, 720p, 480p, etc.).
- **✅ Real-time Validation**: Every link is verified in real-time to ensure it's active and playable before being returned.
- **🖼️ Metadata Enrichment**: Fetches movie titles, posters, and descriptions along with the streaming links.
- **🛡️ Anti-Bot Bypass**: Uses Playwright to simulate real human behavior, bypassing common protections like Cloudflare and DDoS-Guard.
- **⚡ Smart Caching**: Integrated caching system to provide lightning-fast responses for popular requests.
- **🐳 Docker Ready**: Optimized Dockerfile for seamless deployment on Render, Railway, or any cloud provider.

## 🛠️ Technology Stack
- **FastAPI**: High-performance Python web framework.
- **Playwright**: Industry-leading browser automation and network interception.
- **Uvicorn**: Lightning-fast ASGI server.
- **Docker**: Containerization for consistent environments.

## 🚀 Quick Start

### Deployment on Render
1. Link your GitHub repository.
2. Render will automatically detect `render.yaml` and `Dockerfile`.
3. The build process will install all necessary Chromium dependencies.

### Local Development
```bash
git clone https://github.com/X4-DevelopmentStudio/Omni-Stream.git
cd Omni-Stream
pip install -r requirements.txt
playwright install chromium
python main.py
```

## 📖 API Documentation
- **Endpoint**: `/extract`
- **Parameters**:
  - `url`: The URL of the target movie/series page.
  - `bypass_cache`: (Optional) Set to `true` to force a fresh extraction.

### Example Response
```json
{
  "metadata": {
    "title": "Hellhound (2024) - WeCima",
    "poster": "https://wecima.gold/posters/hellhound.jpg"
  },
  "streams": [
    {
      "quality": "1080p",
      "url": "https://stream.server.com/1080/playlist.m3u8",
      "valid": true
    },
    {
      "quality": "720p",
      "url": "https://stream.server.com/720/playlist.m3u8",
      "valid": true
    }
  ],
  "status": "success",
  "timestamp": 1715678901.23
}
```

## 🤝 Contributing
Contributions are welcome! Feel free to open issues or submit pull requests to make Omni-Stream even better.

## ⚖️ License
MIT License
