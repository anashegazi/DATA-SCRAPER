import requests
from bs4 import BeautifulSoup
import json
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

res = requests.get("https://moltaqa-alkhabbazeen.com", headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(res.text, 'html.parser')

scripts = soup.find_all('script')
for s in scripts:
    if s.get('type') == 'application/ld+json' or (s.string and 'social' in s.string.lower()):
        print("FOUND SCRIPT:")
        print(s.string[:500] if s.string else '')
