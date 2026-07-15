
import asyncio
from scrapers import OmniScraper
import json

async def main():
    scraper = OmniScraper()
    tmdb_id = "550" # Fight Club
    print(f"Testing Resolver for TMDB ID: {tmdb_id}")
    result = await scraper.resolve_tmdb(tmdb_id)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
