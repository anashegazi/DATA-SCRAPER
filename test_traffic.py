import requests
from bs4 import BeautifulSoup
import json
import sys
import re

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_similarweb_data(domain):
    url = f"https://data.similarweb.com/api/v1/data?domain={domain}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            visits = data.get('Engagments', {}).get('Visits')
            return visits
    except Exception as e:
        pass
    return None

def get_hypestat_data(domain):
    url = f"https://hypestat.com/info/{domain}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text()
            # Look for daily/monthly visitors
            match = re.search(r'([\d,]+)\+?\s*(?:daily|monthly|visitors|unique visitors)', text, re.IGNORECASE)
            if match:
                return match.group(1)
            # Look for visitor stats in page text
            match2 = re.search(r'(\d[\d,]*)\s*visitors per day', text, re.IGNORECASE)
            if match2:
                daily = int(match2.group(1).replace(',', ''))
                return daily * 30
    except Exception as e:
        pass
    return None

def get_site_stats(domain):
    sw = get_similarweb_data(domain)
    hs = get_hypestat_data(domain)
    print(f"Domain: {domain} | SimilarWeb Visits: {sw} | Hypestat Est: {hs}")

domains = [
    "villagemarket.com.sa",
    "mathaqshafi.com",
    "wtr.sa",
    "naturespirit.com.sa",
    "miniso.sa",
    "zaadana.com"
]

for d in domains:
    get_site_stats(d)
