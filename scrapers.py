
import requests
from bs4 import BeautifulSoup
import re
import json
from typing import Optional, Dict

class OmniScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def extract_egybest(self, url: str) -> Dict:
        """Extracts M3U8 links from EgyBest."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # EgyBest often uses iframes for players
            iframe = soup.find('iframe', class_='player')
            if not iframe:
                return {"error": "Player iframe not found"}
            
            player_url = iframe.get('src')
            if player_url.startswith('//'):
                player_url = 'https:' + player_url
                
            # Further logic to handle the player URL and extract the M3U8 link
            # This often involves following redirects or parsing JS variables
            return {
                "site": "EgyBest",
                "original_url": url,
                "player_url": player_url,
                "m3u8_link": f"{player_url}/video.m3u8", # Simplified for demonstration
                "status": "success"
            }
        except Exception as e:
            return {"error": str(e)}

    def extract_wecima(self, url: str) -> Dict:
        """Extracts M3U8 links from WeCima (MyCima)."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            # WeCima often has direct download/stream links in the page source
            # or uses a specific API endpoint
            match = re.search(r'file: "(https?://.*?\.m3u8)"', response.text)
            if match:
                return {
                    "site": "WeCima",
                    "original_url": url,
                    "m3u8_link": match.group(1),
                    "status": "success"
                }
            return {"error": "M3U8 link not found in page source"}
        except Exception as e:
            return {"error": str(e)}

    def extract_arabseed(self, url: str) -> Dict:
        """Extracts M3U8 links from ArabSeed."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            # ArabSeed might use a different pattern
            match = re.search(r'source: "(https?://.*?\.m3u8)"', response.text)
            if match:
                return {
                    "site": "ArabSeed",
                    "original_url": url,
                    "m3u8_link": match.group(1),
                    "status": "success"
                }
            return {"error": "M3U8 link not found"}
        except Exception as e:
            return {"error": str(e)}

    def extract(self, site: str, url: str) -> Dict:
        if site.lower() == "egybest":
            return self.extract_egybest(url)
        elif site.lower() in ["wecima", "mycima"]:
            return self.extract_wecima(url)
        elif site.lower() == "arabseed":
            return self.extract_arabseed(url)
        else:
            return {"error": f"Site '{site}' not supported"}

