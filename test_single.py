import requests
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7'
}

r = requests.get("https://anastna.com", headers=headers, verify=False, allow_redirects=True)
print("Status:", r.status_code)
soup = BeautifulSoup(r.text, 'html.parser')
title = soup.find('title')
print("Title:", title.string if title else None)

phone_matches = re.findall(r'(?:\+?966|00966|05)\d{8}|9200\d{5}|800\d{6,7}', r.text)
print("Phones:", set(phone_matches))

emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
print("Emails:", set(emails))
