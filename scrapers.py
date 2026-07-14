
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict
import base64
import json

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
            # WeCima uses heavily obfuscated JS. The player URL is often inside a data attribute or injected via JS.
            
            # Look for the specific player iframe pattern in the response text
            # The iframe might be hidden in a script or data attribute
            match = re.search(r'src="([^"]*akhbarworld\.online[^"]*)"', response.text)
            if not match:
                match = re.search(r'src="([^"]*fastvip\.space[^"]*)"', response.text)
            
            player_url = match.group(1) if match else None
            
            if not player_url:
                # Fallback: Search for any M3U8 links in the text
                m3u8_matches = re.findall(r'(https?://[^\s"]+\.m3u8)', response.text)
                if m3u8_matches:
                    return {
                        "site": "WeCima",
                        "original_url": url,
                        "m3u8_link": m3u8_matches[0],
                        "status": "success"
                    }
                return {"error": "Could not find player or M3U8 link on WeCima"}

            # Decode player URL if it contains encoded data
            if 'mycimafsd=' in player_url:
                try:
                    encoded_data = player_url.split('mycimafsd=')[1]
                    # Handle potential padding issues
                    missing_padding = len(encoded_data) % 4
                    if missing_padding:
                        encoded_data += '=' * (4 - missing_padding)
                    decoded_url = base64.b64decode(encoded_data).decode('utf-8')
                    return {
                        "site": "WeCima",
                        "original_url": url,
                        "player_url": decoded_url,
                        "m3u8_link": f"{decoded_url}/playlist.m3u8",
                        "status": "success"
                    }
                except:
                    pass

            return {
                "site": "WeCima",
                "original_url": url,
                "player_url": player_url,
                "status": "partial_success",
                "note": "Player found, but M3U8 extraction requires further steps"
            }
        except Exception as e:
            return {"error": str(e)}

    def extract_egybest(self, url: str) -> Dict:
        """Extracts M3U8 links from EgyBest."""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            # Look for common player patterns
            match = re.search(r'source: "(https?://.*?\.m3u8)"', response.text)
            if not match:
                match = re.search(r'file: "(https?://.*?\.m3u8)"', response.text)
            
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
