import requests
from bs4 import BeautifulSoup, Comment
import re
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

r = requests.get("https://villagemarket.com.sa/ar", headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(r.text, 'html.parser')

# Remove scripts, styles, and comments
for s in soup(["script", "style", "head"]):
    s.extract()

for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
    comment.extract()

# 1. Tel links
tel_links = set()
for a in soup.find_all('a', href=True):
    href = a['href'].strip()
    if href.startswith('tel:'):
        num = href.replace('tel:', '').strip()
        tel_links.add(num)

print("Cleaned Tel Links:", tel_links)

# 2. Visible Text strict phone regex
visible_text = soup.get_text()

# Strict Saudi mobile: +966 5X XXX XXXX or 05X XXX XXXX
saudi_mobile = set(re.findall(r'(?:\+?966|00966|0)?5\d{8}\b', visible_text))
# Strict Saudi unified: 9200XXXXX
saudi_unified = set(re.findall(r'\b9200\d{5}\b', visible_text))
# Strict Saudi toll-free: 800XXXXXXX
saudi_tollfree = set(re.findall(r'\b800\d{6,7}\b', visible_text))

print("Visible Text Mobiles:", saudi_mobile)
print("Visible Text Unified:", saudi_unified)
print("Visible Text TollFree:", saudi_tollfree)
