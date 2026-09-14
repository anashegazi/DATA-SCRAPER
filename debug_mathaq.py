import requests
from bs4 import BeautifulSoup
import re
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

r = requests.get("https://mathaqshafi.com/ar", headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(r.text, 'html.parser')

print("--- ALL HREFS IN MATHAQSHAFI.COM ---")
links = [a.get('href') for a in soup.find_all('a', href=True)]
for l in links:
    if 'tel:' in l or '966' in l or '5380' in l:
        print("LINK:", l)

print("\n--- ALL RAW 5380 IN HTML ---")
for line in r.text.splitlines():
    if '5380' in line:
        print("LINE:", line.strip()[:150])
