import requests

domains = ["anastna.com", "nataj.com.sa", "fawq-wasf.com.sa", "row.sa"]
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for d in domains:
    for proto in ['https://', 'https://www.', 'http://', 'http://www.']:
        try:
            r = requests.get(proto + d, headers=headers, timeout=5, verify=False)
            print(f"{d} -> {proto + d} SUCCESS ({r.status_code})")
            break
        except Exception as e:
            print(f"{d} -> {proto + d} FAILED: {e}")
