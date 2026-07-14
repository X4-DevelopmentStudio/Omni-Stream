
import asyncio
from scrapers import OmniScraper
import json

async def main():
    scraper = OmniScraper()
    url = "https://wecima.gold/%d9%85%d8%b4%d8%a7%d9%87%d8%af%d8%a9-%d9%81%d9%8a%d9%84%d9%85-hellhound-2024-%d9%85%d8%aa%d8%b1%d8%ac%d9%85/"
    print(f"Testing extraction for: {url}")
    result = await scraper.extract_god_mode(url)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
