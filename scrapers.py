
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
            
            # WeCima often hides the player URL in a way that's hard to find with simple regex
            # Let's try to find all iframe src attributes
            soup = BeautifulSoup(response.text, 'html.parser')
            iframes = soup.find_all('iframe')
            
            player_url = None
            for iframe in iframes:
                src = iframe.get('src')
                if src and ('akhbarworld' in src or 'fastvip' in src or 'stream' in src):
                    player_url = src
                    break
            
            if not player_url:
                # Search for any URL that looks like a player or stream
                matches = re.findall(r'https?://[^\s"]+(?:akhbarworld|fastvip|stream|player)[^\s"]+', response.text)
                if matches:
                    player_url = matches[0]

            if player_url:
                if 'mycimafsd=' in player_url:
                    try:
                        encoded_data = player_url.split('mycimafsd=')[1]
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
                    "note": "Player found, but direct M3U8 requires browser simulation"
                }

            return {"error": "Could not find player on WeCima page"}
        except Exception as e:
            return {"error": str(e)}

    def extract_egybest(self, url: str) -> Dict:
        """Extracts M3U8 links from EgyBest."""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            match = re.search(r'(https?://[^\s"]+\.m3u8)', response.text)
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
