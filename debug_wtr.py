import requests
from bs4 import BeautifulSoup
import re
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

r = requests.get("https://wtr.sa/ar", headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = r.text

print("--- SEARCHING WTR.SA FOR WHATSAPP / CONTACT / PHONE ---")

soup = BeautifulSoup(html, 'html.parser')
all_a = soup.find_all('a')
print(f"Total <a> tags: {len(all_a)}")
for a in all_a:
    href = a.get('href', '')
    text = a.get_text().strip()
    if any(k in href.lower() for k in ['wa', 'whatsapp', 'api.whatsapp', 'tel', 'phone', 'contact']):
        print(f"FOUND A: href='{href}' | text='{text}'")

# Search all raw lines containing whatsapp
for line in html.splitlines():
    if 'whatsapp' in line.lower() or 'wa.me' in line.lower():
        print("RAW LINE:", line.strip()[:200])
