import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import json

def test_domain(domain):
    url = f"https://{domain}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8'
    }
    
    print(f"--- Fetching {domain} ---")
    try:
        res = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"Status Code: {res.status_code}")
        print(f"Final URL: {res.url}")
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Extracts links
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        
        # Phone
        phones = set()
        for link in links:
            if link.startswith('tel:'):
                phones.add(link.replace('tel:', '').strip())
        
        # Phone regex from text
        phone_matches = re.findall(r'(?:\+?966|05)\d{8}|9200\d{5}|800\d{6,7}', res.text)
        phones.update(phone_matches)
        
        # WhatsApp
        whatsapp = set()
        for link in links:
            if any(w in link for w in ['wa.me', 'api.whatsapp.com', 'whatsapp://', 'chat.whatsapp.com']):
                whatsapp.add(link)
                
        # Emails
        emails = set()
        for link in links:
            if link.startswith('mailto:'):
                emails.add(link.replace('mailto:', '').split('?')[0].strip())
        email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)
        for em in email_matches:
            if not em.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
                emails.add(em)
                
        # Social Media
        socials = {
            'facebook': [],
            'instagram': [],
            'tiktok': [],
            'twitter': [],
            'snapchat': [],
            'linkedin': [],
            'youtube': []
        }
        for link in links:
            for platform in socials.keys():
                if platform in link.lower() or (platform == 'twitter' and 'x.com' in link.lower()):
                    if link not in socials[platform]:
                        socials[platform].append(link)
                        
        print(f"Phones: {list(phones)}")
        print(f"WhatsApp: {list(whatsapp)}")
        print(f"Emails: {list(emails)}")
        print(f"Socials: {json.dumps(socials, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"Error fetching {domain}: {e}")

if __name__ == '__main__':
    test_domain("villagemarket.com.sa")
    test_domain("mathaqshafi.com")
