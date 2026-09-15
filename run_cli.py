"""
run_cli.py — سكرابر سريع بلا واجهة (استخدام شخصي)
يقرا الروابط من ملف txt، يفحص كل المتاجر بالتوازي، ويخرج Excel + CSV.

الاستخدام:
    python run_cli.py --links روابطي.txt --fast --workers 200
    python run_cli.py --links روابطي.txt --full --workers 100
    python run_cli.py --links روابطي.txt --fast --workers 256 --out-dir C:\results
"""
import sys
import os
import re
import json
import time
import random
import threading
import argparse
import urllib3
import concurrent.futures
from datetime import datetime

import requests
import pandas as pd
import openpyxl
from tqdm import tqdm

from extractors import harvest_domain, bucket_to_row, SOCIAL_NETWORKS

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RESULTS_FILE = 'partial_results.jsonl'
_lock = threading.Lock()

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
]

TIMEOUT = 5.0

_local = threading.local()


def _get_session():
    if not hasattr(_local, 'session'):
        s = requests.Session()
        s.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        s.verify = False
        _local.session = s
    return _local.session


def fetch_url(url):
    session = _get_session()
    try:
        res = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        if res is None:
            return None
        # Cloudflare JS challenge: "Just a moment..." لا يمكن تجاوزه بـ requests
        if res.status_code in (403, 429, 503):
            ct = res.headers.get('Server', '').lower()
            if 'cloudflare' in ct or 'Just a moment' in (res.text[:200] if res.text else ''):
                return None
        if res.status_code == 200 and len(res.text) > 300:
            return res
    except Exception:
        pass
    return None


def get_tranco_rank(domain):
    try:
        r = requests.get(f"https://tranco-list.eu/api/ranks/domain/{domain}", timeout=3)
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
        return 0, "0 SAR", "غير نشط"

    if tranco_rank and tranco_rank > 0:
        monthly_visits = int(100_000_000_000 / (tranco_rank ** 1.12))
        monthly_visits = max(monthly_visits, 800)
    else:
        base = 800 if any(p in platform for p in ['Salla', 'Zid', 'Shopify', 'WooCommerce', 'سلة', 'زد']) else 300
        monthly_visits = base + random.randint(10, 450)

    if any(p in platform for p in ['Salla', 'Zid', 'Shopify', 'WooCommerce', 'سلة', 'زد']):
        rev_min = int(monthly_visits * 0.01 * 100)
        rev_max = int(monthly_visits * 0.02 * 180)
        rev_str = f"{rev_min:,} - {rev_max:,} SAR"
    else:
        rev_min = int((monthly_visits / 1000) * 15)
        rev_max = int((monthly_visits / 1000) * 45)
        rev_str = f"{rev_min:,} - {rev_max:,} SAR"

    return monthly_visits, rev_str, "نشط"


def error_row(domain):
    bucket = {
        'phones': set(), 'whatsapp': set(), 'emails': set(),
        'socials': {k: set() for k in SOCIAL_NETWORKS},
        'title': '', 'platform': 'غير معروف', 'active': False,
    }
    row = bucket_to_row(domain, bucket)
    row['الزيارات الشهرية التقديرية'] = ''
    row['العوائد الشهرية التقديرية (SAR)'] = ''
    return row


def scrape_worker(domain, fast, use_parallel):
    try:
        bucket = harvest_domain(domain, fetch_url, max_pages=0 if fast else 5, parallel=use_parallel)
        row = bucket_to_row(domain, bucket)
        # الأعمدة موجودة وفارغة ليتم ملؤها يدوياً
        row['الزيارات الشهرية التقديرية'] = ''
        row['العوائد الشهرية التقديرية (SAR)'] = ''
        return row
    except Exception:
        return error_row(domain)


def save_row(row):
    with _lock:
        with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def load_done():
    rows = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        continue
    return rows


def normalize_link(l):
    l = l.strip().replace('https://', '').replace('http://', '').split('/')[0]
    return l.strip(' .')


def read_links(path):
    domains, seen = [], set()
    with open(path, encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = normalize_link(line)
            if d and '.' in d and d not in seen:
                seen.add(d)
                domains.append(d)
    return domains


def write_output(rows_by_domain, ordered, out_dir):
    df = pd.DataFrame([rows_by_domain[d] for d in ordered if d in rows_by_domain])
    base = datetime.now().strftime('نتائج_%Y%m%d_%H%M%S')
    excel_path = os.path.join(out_dir, base + '.xlsx')
    csv_path = os.path.join(out_dir, base + '.csv')

    for attempt in range(5):
        try:
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='البيانات المستخرجة')
            break
        except PermissionError:
            base = datetime.now().strftime(f'نتائج_%Y%m%d_%H%M%S_v{attempt + 2}')
            excel_path = os.path.join(out_dir, base + '.xlsx')
            csv_path = os.path.join(out_dir, base + '.csv')

    return excel_path, csv_path, len(df)


def main():
    p = argparse.ArgumentParser(description='سكرابر المتاجر — بلا واجهة')
    p.add_argument('--links', required=True, help='ملف txt فيه الروابط (سطر لكل رابط)')
    p.add_argument('--fast', action='store_true', help='الوضع السريع: الرئيسية فقط (بدون ترافيك)')
    p.add_argument('--workers', type=int, default=50, help='عدد العمال المتزامنين (افتراضي 50)')
    p.add_argument('--timeout', type=float, default=5.0, help='مهلة الطلب بالثواني (افتراضي 5)')
    p.add_argument('--parallel', action='store_true', help='تفعيل الجرب الموازي للعناوين (قد يسبب حظر Cloudflare)')
    p.add_argument('--out-dir', default='.', help='مجلد حفظ النتائج')
    p.add_argument('--fresh', action='store_true', help='تجاهل النتائج المحفوظة والبدء من الأول')
    args = p.parse_args()

    global TIMEOUT
    TIMEOUT = args.timeout
    fast = args.fast
    use_parallel = args.parallel

    if not os.path.exists(args.links):
        print(f'[!] الملف غير موجود: {args.links}')
        sys.exit(1)

    domains = read_links(args.links)
    if not domains:
        print('[!] مفيش روابط صالحة في الملف.')
        sys.exit(1)

    os.makedirs(args.out_dir, exist_ok=True)

    done_domains = set()
    done_rows = {}
    if not args.fresh:
        for r in load_done():
            d = r.get('الموقع (Domain)')
            if d:
                done_domains.add(d)
                done_rows[d] = r
    pending = [d for d in domains if d not in done_domains]
    total = len(domains)

    print(f'[*] إجمالي: {total} دومين | تم سابقاً: {len(done_domains)} | المتبقي: {len(pending)}')
    print(f'[*] الوضع: {"سريع (رئيسية فقط)" if fast else "كامل (داخلي + ترافيك)"} | عمال: {args.workers} | مهلة: {args.timeout}s')

    start = time.time()
    completed = 0

    if pending:
        with tqdm(total=len(pending), desc='فحص', unit='موقع', bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as bar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = {executor.submit(scrape_worker, d, fast, use_parallel): d for d in pending}
                try:
                    for future in concurrent.futures.as_completed(futures):
                        d = futures[future]
                        try:
                            row = future.result()
                        except Exception:
                            row = error_row(d)
                        save_row(row)
                        done_rows[d] = row
                        completed += 1
                        bar.update(1)
                except KeyboardInterrupt:
                    print('\n[!] أُوقف بواسطة المستخدم — النتائج المحفوظة مبقية.')

    print(f'[*] الزمن الإجمالي: {time.time() - start:.1f} ثانية')
    print("[*] جاري كتابة الملفات...")

    excel_path, csv_path, n_rows = write_output(done_rows, domains, args.out_dir)
    print(f'[✔] تمت معالجة {n_rows} دومين ناجح من {total}.')
    print(f'    Excel: {excel_path}')
    print(f'    CSV:   {csv_path}')


if __name__ == '__main__':
    main()