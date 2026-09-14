import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import sys
import urllib3
import traceback

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7'
}

def test(domain):
    try:
        url = f"https://{domain}"
        res = requests.get(url, headers=HEADERS, timeout=10, verify=False, allow_redirects=True)
        print("DOM:", domain, "STATUS:", res.status_code, "LEN:", len(res.text))
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.find('title')
        print("TITLE:", title.string if title else 'No title')
    except Exception as e:
        print("ERR:", domain, e)
        traceback.print_exc()

test("villagemarket.com.sa")
test("mathaqshafi.com")
