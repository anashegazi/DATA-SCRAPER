import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

try:
    res = requests.get("https://villagemarket.com.sa", headers=headers, timeout=10, allow_redirects=True, verify=False)
    print("RES:", res.status_code, len(res.text))
except Exception as e:
    print("ERROR:", e)
