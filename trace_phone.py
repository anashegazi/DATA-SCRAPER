import requests
from bs4 import BeautifulSoup
import re
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

r = requests.get("https://villagemarket.com.sa/ar", headers={'User-Agent': 'Mozilla/5.0'})
html = r.text

print("--- SEARCHING FOR PHONE NUMBERS IN VILLAGEMARKET.COM.SA ---")

# Check all tel: links
soup = BeautifulSoup(html, 'html.parser')
tel_links = [a.get('href') for a in soup.find_all('a', href=True) if 'tel:' in a.get('href')]
print("TEL LINKS:", tel_links)

# Check all raw matches
for num in ['55124901', '55824808', '800186685']:
    matches = [line.strip() for line in html.splitlines() if num in line]
    print(f"\nMatches for '{num}':")
    for m in matches[:5]:
        print("  -->", m[:150])
