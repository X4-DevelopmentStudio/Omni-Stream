
import requests
import json

def test_proxy_logic():
    # Simulated data from the scraper
    target_url = "https://fastvip.space/stream/ni4WyatlHmZu2Fo4CHreGA/kjhhiuahiuhgihdf/1784062628/58124787/master.m3u8"
    referer = "https://wecima.gold/"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    print(f"Testing Proxy Logic for: {target_url}")
    
    # Step 1: Test without headers (Should fail with 403)
    try:
        r1 = requests.get(target_url, timeout=5)
        print(f"Direct request status: {r1.status_code}")
    except Exception as e:
        print(f"Direct request failed: {e}")
        
    # Step 2: Test with correct headers (What the proxy does)
    headers = {
        "User-Agent": user_agent,
        "Referer": referer
    }
    try:
        r2 = requests.get(target_url, headers=headers, timeout=10)
        print(f"Proxied request status: {r2.status_code}")
        if r2.status_code == 200:
            print("SUCCESS: Proxy logic bypasses 403!")
            print(f"Content preview: {r2.text[:100]}")
    except Exception as e:
        print(f"Proxied request failed: {e}")

if __name__ == "__main__":
    test_proxy_logic()
