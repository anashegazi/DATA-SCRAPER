import requests
from bs4 import BeautifulSoup
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def test_salla_alt(domain):
    # Try /ar, /robots.txt, or salla.sa/
    username = domain.split('.')[0]
    urls = [
        f"https://{domain}/ar",
        f"https://salla.sa/{username}",
        f"https://{domain}/sitemap.xml"
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(r.text, 'html.parser')
            title = soup.find('title')
            print(f"URL: {url} -> Status: {r.status_code} | Title: {title.string.strip() if title else 'No title'}")
        except Exception as e:
            print(f"URL: {url} -> Error: {e}")

test_salla_alt("villagemarket.com.sa")
test_salla_alt("mathaqshafi.com")
