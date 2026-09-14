import requests
from bs4 import BeautifulSoup
import re
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def test_siteprice(domain):
    url = f"https://www.siteprice.org/website-worth/{domain}"
    try:
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Look for Daily Unique Visitors / Daily Pageviews / Estimated Value
            text = soup.get_text()
            views = re.findall(r'Daily Unique Visitors:\s*([\d,]+)', text)
            value = re.findall(r'Estimated Website Value:\s*\$([\d,]+)', text)
            revenue = re.findall(r'Daily Revenue:\s*\$([\d,]+|\d+)', text)
            return {
                'daily_visitors': views[0] if views else None,
                'daily_revenue': revenue[0] if revenue else None,
                'est_value': value[0] if value else None
            }
    except Exception as e:
        return {'error': str(e)}
    return None

def test_tranco(domain):
    try:
        r = requests.get(f"https://tranco-list.eu/api/ranks/domain/{domain}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            ranks = data.get('ranks', [])
            if ranks:
                return ranks[0].get('rank')
    except Exception as e:
        pass
    return None

domains = ["villagemarket.com.sa", "mathaqshafi.com", "wtr.sa", "miniso.sa", "zaadana.com"]

for d in domains:
    sp = test_siteprice(d)
    tr = test_tranco(d)
    print(f"Domain: {d} | SitePrice: {sp} | Tranco Rank: {tr}")
