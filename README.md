# 💎 Omni-Stream Enterprise Edition

The most powerful, comprehensive Arabic streaming extraction engine on GitHub. Built for developers who need real, production-ready streaming data.

## 🚀 Enterprise Features
- **🎬 Universal Video Extraction**: Intercepts M3U8/HLS streams from any player using network-level monitoring.
- **💬 Subtitle Discovery**: Automatically captures subtitle tracks (`.vtt`, `.srt`) in multiple languages (Arabic, English, etc.).
- **🛡️ Playback Header Generation**: Provides the exact `Referer` and `User-Agent` headers required to bypass hotlink protection in third-party players (VLC, ExoPlayer, Video.js).
- **🕵️ User-Agent Rotation**: Rotates between modern browser profiles to evade detection and rate-limiting.
- **📑 Rich Metadata**: Deep-scrapes OpenGraph and Meta tags for titles, posters, and full descriptions.
- **⚡ Performance Optimized**: Integrated caching and async execution for high-concurrency environments.

## 🛠️ API Reference
### `GET /extract`
Extract all available assets from a URL.

**Query Params:**
- `url`: The full link to the streaming page.
- `bypass_cache`: (Optional) `true` to force fresh extraction.

**Example Response:**
```json
{
  "metadata": {
    "title": "Karate Kid: Legends (2025)",
    "poster": "https://wecima.gold/poster.jpg",
    "description": "The latest installment in the Karate Kid saga..."
  },
  "streams": [
    { "type": "hls", "url": "https://cdn.com/stream.m3u8", "headers": { "Referer": "..." } }
  ],
  "subtitles": [
    { "language": "AR", "url": "https://cdn.com/ar.vtt", "format": "VTT" },
    { "language": "EN", "url": "https://cdn.com/en.vtt", "format": "SRT" }
  ],
  "playback_requirements": {
    "headers": { "User-Agent": "...", "Referer": "..." }
  }
}
```

## 🐳 Deployment
Optimized for **Render** and **Railway**. The `Dockerfile` handles all system-level dependencies for Playwright and Chromium.

## ⚖️ License
MIT
