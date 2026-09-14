import requests
import json
import re
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

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def clean_phone(phone):
    phone = re.sub(r'[^\d+]', '', phone)
    if phone.startswith('00966'):
        phone = '+' + phone[2:]
    elif phone.startswith('966'):
        phone = '+' + phone
    elif phone.startswith('05') and len(phone) == 10:
        phone = '+966' + phone[1:]
    return phone

for dom in sample_domains:
    try:
        r = requests.get(f"https://{dom}/ar", headers=headers, timeout=6)
        html = r.text
        
        # Search for whatsapp in salla json config
        wa_config = re.findall(r'"whatsapp":\s*"([^"]+)"', html, re.IGNORECASE)
        mobile_config = re.findall(r'"mobile":\s*"([^"]+)"|"phone":\s*"([^"]+)"', html, re.IGNORECASE)
        
        wa_found = set()
        for w in wa_config:
            if w.strip():
                wa_found.add(clean_phone(w))
                
        print(f"Domain: {dom:25} | Salla WA Config: {list(wa_found)}")
    except Exception as e:
        print(f"Domain: {dom:25} | Error: {e}")
