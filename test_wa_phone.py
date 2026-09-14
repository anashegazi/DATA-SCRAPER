import requests
from bs4 import BeautifulSoup
import re
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def clean_phone(phone):
    phone = re.sub(r'[^\d+]', '', phone)
    if phone.startswith('00966'):
        phone = '+' + phone[2:]
    elif phone.startswith('966'):
        phone = '+' + phone
    elif phone.startswith('05') and len(phone) == 10:
        phone = '+966' + phone[1:]
    return phone

def is_valid_phone(phone):
    clean = re.sub(r'[^\d+]', '', phone)
    if clean.startswith('+9665') and len(clean) == 13:
        return True
    if clean.startswith('05') and len(clean) == 10:
        return True
    if clean.startswith('9200') and len(clean) == 9:
        return True
    if clean.startswith('800') and len(clean) in [9, 10]:
        return True
    return False

# Test extracting phone numbers from WhatsApp URLs
wa_url = "https://wa.me/+966538089042?text=نراسلكم من متجر المذاق الشافي للعسل والتمور%0A"
match = re.search(r'(?:\+?966|00966|0)?5\d{8}\b', wa_url)
if match:
    cp = clean_phone(match.group(0))
    print("Extracted Phone from WhatsApp:", cp, "Valid:", is_valid_phone(cp))
