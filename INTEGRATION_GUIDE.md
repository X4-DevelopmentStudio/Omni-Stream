# 📱 Omni-Stream API Integration Guide

This guide explains how to integrate the Omni-Stream API service into your mobile or web application to automate video link extraction.

## 🔗 API Endpoint
`GET https://omni-stream-3zr7.onrender.com/extract?url={MOVIE_URL}`

## 🛠️ Integration Examples

### 1. JavaScript (Web / React Native)
```javascript
async function getVideoStream(movieUrl) {
    const apiUrl = `https://omni-stream-3zr7.onrender.com/extract?url=${encodeURIComponent(movieUrl)}`;
    
    try {
        const response = await fetch(apiUrl);
        const data = await response.json();
        
        if (data.success && data.streams.length > 0) {
            const m3u8Link = data.streams[0].url;
            console.log("Play this link:", m3u8Link);
            // Initialize your player with m3u8Link and data.headers
            return m3u8Link;
        }
    } catch (error) {
        console.error("Extraction failed", error);
    }
}
```

### 2. Flutter (Dart)
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<String?> fetchM3u8(String movieUrl) async {
  final response = await http.get(
    Uri.parse('https://omni-stream-3zr7.onrender.com/extract?url=$movieUrl')
  );

  if (response.statusCode == 200) {
    final data = json.decode(response.body);
    if (data['success'] && data['streams'].isNotEmpty) {
      return data['streams'][0]['url'];
    }
  }
  return null;
}
```

### 3. Java (Android)
```java
// Using OkHttp
OkHttpClient client = new OkHttpClient();
String movieUrl = "https://wecima.gold/...";
Request request = new Request.Builder()
    .url("https://omni-stream-3zr7.onrender.com/extract?url=" + movieUrl)
    .build();

client.newCall(request).enqueue(new Callback() {
    @Override
    public void onResponse(Call call, Response response) throws IOException {
        String jsonData = response.body().string();
        // Parse JSON and get streams[0].url
    }
});
```

## ⚠️ Important: Playback Headers
Some streaming servers check for the `Referer` and `User-Agent`. When initializing your video player (ExoPlayer, Video.js, etc.), make sure to pass the headers returned by the API:

```json
"headers": {
    "User-Agent": "Mozilla/5.0...",
    "Referer": "https://wecima.gold/..."
}
```
