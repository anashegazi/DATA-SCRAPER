import requests
import json
import re
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

res = requests.get("https://moltaqa-alkhabbazeen.com", headers={'User-Agent': 'Mozilla/5.0'})
match = re.search(r'salla\.event\.dispatchEvents\((.*?)\);', res.text, re.DOTALL)
if match:
    try:
        data = json.loads(match.group(1))
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    except Exception as e:
        print("Error parsing json:", e)
else:
    print("Match not found")
