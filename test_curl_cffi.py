from curl_cffi import requests
from bs4 import BeautifulSoup
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

domains = [
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

for dom in domains:
    try:
        r = requests.get(f"https://{dom}", impersonate="chrome120", timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find('title')
        print(f"[SUCCESS] {dom} -> Status: {r.status_code} | Title: {title.string.strip() if title else 'No title'}")
    except Exception as e:
        print(f"[FAIL] {dom} -> Error: {e}")
