import cloudscraper
import requests
from bs4 import BeautifulSoup
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

def test_cloudscraper(domain):
    try:
        r = scraper.get(f"https://{domain}")
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find('title')
        print(f"[CS] {domain} -> Status: {r.status_code} | Title: {title.string.strip() if title else 'No title'}")
    except Exception as e:
        print(f"[CS FAIL] {domain} -> {e}")

test_cloudscraper("villagemarket.com.sa")
test_cloudscraper("mathaqshafi.com")
