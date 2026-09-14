import requests
from bs4 import BeautifulSoup
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7'
}

def check(domain):
    try:
        r = requests.get(f"https://{domain}", headers=headers, timeout=10, verify=True)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find('title')
        print(f"{domain} -> Status: {r.status_code} | Title: {title.string.strip() if title else 'No Title'}")
    except Exception as e:
        print(f"{domain} -> Error: {e}")

check("villagemarket.com.sa")
check("mathaqshafi.com")
check("anastna.com")
check("nataj.com.sa")
