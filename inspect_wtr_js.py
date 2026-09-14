import requests
from bs4 import BeautifulSoup
import re
import json
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

r = requests.get("https://wtr.sa/ar", headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = r.text

print("--- SEARCHING ALL NUMBERS & WHATSAPP DATA IN WTR.SA ---")

# Search for any phone number pattern in full HTML
phones = re.findall(r'(?:\+?966|00966|0)?5\d{8}\b', html)
print("ALL SAUDI MOBILE MATCHES IN HTML:", set(phones))

# Search for whatsapp inside script tags
matches = re.findall(r'https?://[^\s"\'<>]*whatsapp[^\s"\'<>]*', html, re.IGNORECASE)
print("ALL WHATSAPP URL MATCHES IN HTML:", set(matches))

# Search for wa.me in HTML
wame = re.findall(r'https?://[^\s"\'<>]*wa\.me[^\s"\'<>]*', html, re.IGNORECASE)
print("ALL WA.ME MATCHES IN HTML:", set(wame))

# Search for salla-whatsapp or chat custom elements or salla store config
salla_config = re.findall(r'"mobile":\s*"([^"]+)"|"phone":\s*"([^"]+)"|"whatsapp":\s*"([^"]+)"', html, re.IGNORECASE)
print("SALLA CONFIG MATCHES:", salla_config)
