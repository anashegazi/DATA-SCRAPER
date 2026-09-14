import requests
from bs4 import BeautifulSoup, Comment
import re
import urllib.parse
import json
import concurrent.futures
import pandas as pd
import sys
import os
import time
import random
import urllib3
import openpyxl

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]

def get_tranco_rank(domain):
    try:
        r = requests.get(f"https://tranco-list.eu/api/ranks/domain/{domain}", timeout=4)
        if r.status_code == 200:
            data = r.json()
            ranks = data.get('ranks', [])
            if ranks:
                return ranks[0].get('rank')
    except Exception:
        pass
    return None

def estimate_metrics(tranco_rank, platform, is_active):
    if not is_active:
        return 0, "0 SAR", "الموقع غير نشط"
        
    if tranco_rank and tranco_rank > 0:
        if tranco_rank <= 100000:
            monthly_visits = int(50000000 / (tranco_rank ** 0.65))
        elif tranco_rank <= 1000000:
            monthly_visits = int(20000000 / (tranco_rank ** 0.72))
        else:
            monthly_visits = int(10000000 / (tranco_rank ** 0.8))
        monthly_visits = max(monthly_visits, 1200)
    else:
        monthly_visits = 1200 if any(p in platform for p in ['Salla', 'Zid', 'Shopify', 'WooCommerce', 'سلة', 'زد']) else 500

    if any(p in platform for p in ['Salla', 'Zid', 'Shopify', 'WooCommerce', 'سلة', 'زد']):
        rev_min = int(monthly_visits * 0.01 * 100)
        rev_max = int(monthly_visits * 0.02 * 180)
        rev_str = f"{rev_min:,} - {rev_max:,} SAR"
    else:
        rev_min = int((monthly_visits / 1000) * 15)
        rev_max = int((monthly_visits / 1000) * 45)
        rev_str = f"{rev_min:,} - {rev_max:,} SAR"
        
    return monthly_visits, rev_str, "نشط"

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
    if clean.startswith('+9665') and len(clean) in [13, 14]:
        return True
    if clean.startswith('05') and len(clean) in [10, 11]:
        return True
    if clean.startswith('9200') and len(clean) == 9:
        return True
    if clean.startswith('800') and len(clean) in [9, 10]:
        return True
    return False

def fetch_url(url):
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    try:
        res = requests.get(url, headers=headers, timeout=10, allow_redirects=True, verify=False)
        if res and len(res.text) > 300:
            return res
    except Exception:
        pass
    return None

def scrape_domain(domain):
    print(f"[+] Scraping domain with Salla JSON config extraction: {domain}")
    item = {
        'Domain': domain,
        'Site Title': '',
        'Platform': 'Unknown',
        'Status': 'Error',
        'Phones': '',
        'WhatsApp': '',
        'Email': '',
        'Facebook': '',
        'Instagram': '',
        'TikTok': '',
        'Twitter/X': '',
        'Snapchat': '',
        'LinkedIn': '',
        'YouTube': '',
        'Monthly Visits (Est)': 0,
        'Est Monthly Revenue (SAR)': '0 SAR',
        'Tranco Global Rank': 'N/A'
    }

    res = None
    target_urls = [
        f"https://{domain}/ar",
        f"https://www.{domain}/ar",
        f"https://{domain}",
        f"https://www.{domain}"
    ]
    for url in target_urls:
        res = fetch_url(url)
        if res and res.status_code == 200:
            break

    if not res:
        item['Status'] = 'غير متاح'
        return item

    html_content = res.text
    soup = BeautifulSoup(html_content, 'html.parser')
    item['Status'] = 'نشط'

    # Site Title
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        item['Site Title'] = title_tag.string.strip()

    # Detect platform
    page_text_lower = html_content.lower()
    if 'salla.sa' in page_text_lower or 'cdn.salla.sa' in page_text_lower or 'twilight' in page_text_lower:
        item['Platform'] = 'Salla (سلة)'
    elif 'zid.sa' in page_text_lower or 'cdn.zid.sa' in page_text_lower or 'zid-store' in page_text_lower:
        item['Platform'] = 'Zid (زد)'
    elif 'shopify' in page_text_lower:
        item['Platform'] = 'Shopify'
    elif 'wp-content' in page_text_lower or 'woocommerce' in page_text_lower:
        item['Platform'] = 'WooCommerce/WP'

    phones = set()
    whatsapp_links = set()

    # 1. Parse JSON config objects (Salla / Zid / Shopify config in HTML scripts)
    wa_json = re.findall(r'"whatsapp":\s*"([^"]+)"', html_content, re.IGNORECASE)
    phone_json = re.findall(r'"phone":\s*"([^"]+)"|"mobile":\s*"([^"]+)"', html_content, re.IGNORECASE)

    for w in wa_json:
        w_str = w.strip()
        if w_str:
            cp = clean_phone(w_str)
            if is_valid_phone(cp):
                phones.add(cp)
                whatsapp_links.add(f"https://wa.me/{cp.replace('+', '')}")

    for p_tuple in phone_json:
        for p in p_tuple:
            if p.strip():
                cp = clean_phone(p.strip())
                if is_valid_phone(cp):
                    phones.add(cp)

    # 2. Extract links
    links = [a.get('href') for a in soup.find_all('a', href=True)]
    for link in links:
        if link.startswith('tel:'):
            p = clean_phone(link.replace('tel:', '').strip())
            if is_valid_phone(p):
                phones.add(p)
        if any(w in link.lower() for w in ['wa.me', 'api.whatsapp.com', 'whatsapp://', 'chat.whatsapp.com']):
            if not '${' in link and not 'undefined' in link:
                whatsapp_links.add(link)
                wa_match = re.search(r'(?:\+?966|00966|0)?5\d{8,9}\b', link)
                if wa_match:
                    cp = clean_phone(wa_match.group(0))
                    if is_valid_phone(cp):
                        phones.add(cp)

    # 3. Clean DOM text scan
    soup_clean = BeautifulSoup(html_content, 'html.parser')
    for element in soup_clean(["script", "style", "head", "noscript"]):
        element.extract()
    for comment in soup_clean.find_all(string=lambda text: isinstance(text, Comment)):
        element.extract() if hasattr(comment, 'extract') else None

    visible_text = soup_clean.get_text()
    raw_mobiles = re.findall(r'(?:\+?966|00966|0)?5\d{8,9}\b', visible_text)
    raw_unified = re.findall(r'\b9200\d{5}\b', visible_text)
    raw_tollfree = re.findall(r'\b800\d{6,7}\b', visible_text)

    for p in raw_mobiles + raw_unified + raw_tollfree:
        cp = clean_phone(p)
        if is_valid_phone(cp):
            phones.add(cp)

    # Emails
    emails = set()
    for link in links:
        if link.startswith('mailto:'):
            emails.add(link.replace('mailto:', '').split('?')[0].strip())
    email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', visible_text)
    for em in email_matches:
        if not em.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js', '.woff', '.ttf')):
            emails.add(em)

    # Social Media
    social_map = {
        'Facebook': ['facebook.com', 'fb.com', 'fb.me'],
        'Instagram': ['instagram.com'],
        'TikTok': ['tiktok.com'],
        'Twitter/X': ['twitter.com', 'x.com'],
        'Snapchat': ['snapchat.com'],
        'LinkedIn': ['linkedin.com'],
        'YouTube': ['youtube.com', 'youtu.be']
    }

    found_socials = {k: set() for k in social_map}

    for link in links:
        l_lower = link.lower()
        for platform, domains in social_map.items():
            if any(d in l_lower for d in domains):
                if not any(x in l_lower for x in ['share', 'intent/tweet', 'sharer.php', 'salla.sa', 'widgets', 'schema.org', 'w3.org']):
                    found_socials[platform].add(link)

    # Tranco Rank & Traffic Estimates
    rank = get_tranco_rank(domain)
    visits, est_rev, _ = estimate_metrics(rank, item['Platform'], item['Status'] == 'نشط')

    item['Phones'] = " | ".join(sorted(list(phones))) if phones else ""
    item['WhatsApp'] = " | ".join(sorted(list(whatsapp_links))) if whatsapp_links else ""
    item['Email'] = " | ".join(sorted(list(emails))) if emails else ""
    item['Facebook'] = " | ".join(sorted(list(found_socials['Facebook']))) if found_socials['Facebook'] else ""
    item['Instagram'] = " | ".join(sorted(list(found_socials['Instagram']))) if found_socials['Instagram'] else ""
    item['TikTok'] = " | ".join(sorted(list(found_socials['TikTok']))) if found_socials['TikTok'] else ""
    item['Twitter/X'] = " | ".join(sorted(list(found_socials['Twitter/X']))) if found_socials['Twitter/X'] else ""
    item['Snapchat'] = " | ".join(sorted(list(found_socials['Snapchat']))) if found_socials['Snapchat'] else ""
    item['LinkedIn'] = " | ".join(sorted(list(found_socials['LinkedIn']))) if found_socials['LinkedIn'] else ""
    item['YouTube'] = " | ".join(sorted(list(found_socials['YouTube']))) if found_socials['YouTube'] else ""
    item['Monthly Visits (Est)'] = f"{visits:,}"
    item['Est Monthly Revenue (SAR)'] = est_rev
    item['Tranco Global Rank'] = f"{rank:,}" if rank else 'N/A'

    return item

def save_excel_formatted(df, excel_path, csv_path):
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Scraped Contacts"
    
    headers = list(df.columns)
    ws.append(headers)
    
    for row in df.itertuples(index=False):
        row_data = []
        for val in row:
            row_data.append(str(val) if val is not None else "")
        ws.append(row_data)

    wb.save(excel_path)

def main():
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

    results = []
    print(f"[*] Executing Salla JSON contact extraction scraper on {len(sample_domains)} domains...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scrape_domain, dom): dom for dom in sample_domains}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)

    df = pd.DataFrame(results)
    df['Domain_Cat'] = pd.Categorical(df['Domain'], categories=sample_domains, ordered=True)
    df = df.sort_values('Domain_Cat').drop(columns=['Domain_Cat'])

    excel_path = r"c:\Users\anasb\Downloads\SCRAPER\sample_contacts_and_metrics.xlsx"
    csv_path = r"c:\Users\anasb\Downloads\SCRAPER\sample_contacts_and_metrics.csv"

    for attempt in range(5):
        try:
            save_excel_formatted(df, excel_path, csv_path)
            break
        except PermissionError:
            excel_path = f"c:\\Users\\anasb\\Downloads\\SCRAPER\\sample_contacts_and_metrics_v2.xlsx"
            csv_path = f"c:\\Users\\anasb\\Downloads\\SCRAPER\\sample_contacts_and_metrics_v2.csv"

    print(f"\n[✔] Completed Scraping & Export!")
    print(f"Excel File: {excel_path}")
    print(f"CSV File: {csv_path}")

if __name__ == '__main__':
    main()
