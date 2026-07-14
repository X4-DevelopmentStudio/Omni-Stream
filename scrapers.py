
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict
import base64

class OmniScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://wecima.gold/'
        }

    def extract_wecima(self, url: str) -> Dict:
        """Extracts M3U8 links from WeCima (MyCima)."""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # WeCima often embeds the player in an iframe
            iframes = soup.find_all('iframe')
            player_url = None
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'akhbarworld.online' in src or 'fastvip.space' in src:
                    player_url = src
                    break
            
            if not player_url:
                # Try to find direct video source in script tags
                match = re.search(r'file: "(https?://.*?\.m3u8)"', response.text)
                if match:
                    return {
                        "site": "WeCima",
                        "original_url": url,
                        "m3u8_link": match.group(1),
                        "status": "success"
                    }
                return {"error": "Player not found on WeCima page"}

            # If we found a player URL, we might need to fetch its content
            # Note: Real extraction might require handling base64 encoded params
            if 'mycimafsd=' in player_url:
                encoded_url = player_url.split('mycimafsd=')[1]
                decoded_url = base64.b64decode(encoded_url).decode('utf-8')
                return {
                    "site": "WeCima",
                    "original_url": url,
                    "player_url": decoded_url,
                    "m3u8_link": f"{decoded_url}/playlist.m3u8", # Simplified pattern
                    "status": "success"
                }

            return {
                "site": "WeCima",
                "original_url": url,
                "player_url": player_url,
                "status": "partial_success",
                "note": "Manual extraction from player URL might be needed"
            }
        except Exception as e:
            return {"error": str(e)}

    def extract_egybest(self, url: str) -> Dict:
        """Extracts M3U8 links from EgyBest."""
        try:
            # EgyBest has high protection, often requiring specific cookies or headers
            response = requests.get(url, headers=self.headers, timeout=15)
            # Look for common player patterns
            match = re.search(r'source: "(https?://.*?\.m3u8)"', response.text)
            if match:
                return {
                    "site": "EgyBest",
                    "original_url": url,
                    "m3u8_link": match.group(1),
                    "status": "success"
                }
            return {"error": "M3U8 link not found on EgyBest"}
        except Exception as e:
            return {"error": str(e)}

    def extract(self, site: str, url: str) -> Dict:
        if site.lower() in ["wecima", "mycima"]:
            return self.extract_wecima(url)
        elif site.lower() == "egybest":
            return self.extract_egybest(url)
        else:
            # Fallback generic extraction
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                match = re.search(r'(https?://[^\s"]+\.m3u8)', response.text)
                if match:
                    return {
                        "site": site,
                        "original_url": url,
                        "m3u8_link": match.group(1),
                        "status": "success"
                    }
                return {"error": f"Could not extract M3U8 from {site}"}
            except Exception as e:
                return {"error": str(e)}

