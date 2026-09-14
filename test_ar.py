import requests
from bs4 import BeautifulSoup
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sample_domains = [
    "villagemarket.com.sa",
    "mathaqshafi.com",
    "wtr.sa",
    "naturespirit.com.sa",
    "savvy.sa",
    "halqa.sa",
    "moltaqa-alkhabbazeen.com",
    "hai.sa",
    "getbakery8.com",
    "zaadana.com",
    "shub.coffee",
    "miniso.sa",
    "freshflavor.store",
    "store-jouna.com",
    "safwat-aljawf.com",
    "arriyadhroaster.com",
    "anastna.com",
    "nataj.com.sa",
    "fawq-wasf.com.sa",
    "row.sa"
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for dom in sample_domains:
    url = f"https://{dom}/ar"
    try:
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find('title')
        t_str = title.string.strip() if title else 'No Title'
        print(f"[SUCCESS {r.status_code}] {dom} -> {t_str}")
    except Exception as e:
        print(f"[ERR] {dom} -> {e}")
