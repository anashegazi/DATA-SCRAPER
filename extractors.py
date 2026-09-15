# -*- coding: utf-8 -*-
"""
extractors.py — استخراج شامل للأرقام والإيميلات وروابط السوشيال ميديا
يستخدم مع app.py / scraper_full.py

الفلسفة: منحذفش أي مصدر. بنقرأ الـ HTML الخام + النص المرئي + الـ JSON-LD
+ الـ meta tags + الـ script configs، وبعدين نفلتر في الآخر مش في الأول.
"""

import re
import json
import html as htmllib
import urllib.parse
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# 1) تنظيف وتطبيع الأرقام
# ---------------------------------------------------------------------------

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

# أرقام مش هواتف: سجل تجاري، ضريبي، IBAN، تواريخ، إحداثيات، وأرقام وهمية
JUNK_PATTERNS = [
    r'^\d{15}$',          # الرقم الضريبي السعودي
    r'^\d{10}$',          # ممكن يكون سجل تجاري — بنسمح بيه بس لو بادئ بـ 05
    r'^(19|20)\d{2}$',    # سنوات
    r'^0{4,}',
    r'^1{6,}|^2{6,}|^3{6,}|^9{6,}',  # أرقام مكررة (placeholders)
    r'^(966)?123456789\d*$',         # أرقام تجريبية افتراضية في قوالب المنصات
]


def normalize_digits(text: str) -> str:
    """يحول الأرقام العربية/الفارسية لإنجليزية ويفك HTML entities."""
    return htmllib.unescape(text or "").translate(ARABIC_DIGITS)


def clean_phone(raw: str, default_cc: str = "966") -> str:
    """يرجّع الرقم بصيغة E.164 قدر الإمكان."""
    raw = normalize_digits(str(raw))
    # نشيل امتدادات زي ext. / تحويلة
    raw = re.split(r'(?:ext|x|تحويلة)\.?\s*\d+$', raw, flags=re.I)[0]
    p = re.sub(r'[^\d+]', '', raw)
    p = re.sub(r'(?<!^)\+', '', p)  # + في النص بس

    if p.startswith('00'):
        p = '+' + p[2:]
    elif p.startswith(default_cc) and len(p) >= 11:
        p = '+' + p
    elif p.startswith('05') and len(p) == 10:
        p = '+' + default_cc + p[1:]
    elif p.startswith('01') and len(p) == 10 and default_cc == '966':
        p = '+' + default_cc + p[1:]      # أرضي سعودي
    elif p.startswith('5') and len(p) == 9:
        p = '+' + default_cc + p
    return p


def is_valid_phone(phone: str) -> bool:
    """فلترة نهائية — أوسع من النسخة القديمة عشان منفوّتش حاجة."""
    p = re.sub(r'[^\d+]', '', normalize_digits(phone))
    digits = p.lstrip('+')

    if len(digits) < 7 or len(digits) > 15:
        return False
    if len(set(digits)) <= 2:            # 0000000 / 1212121
        return False
    for jp in JUNK_PATTERNS[1:]:
        if re.match(jp, digits):
            return False

    # سعودي
    if p.startswith('+9665') and len(digits) == 12:
        return True
    if p.startswith('+9661') and len(digits) == 12:      # أرضي
        return True
    if digits.startswith('9200') and len(digits) == 9:   # موحد
        return True
    if digits.startswith('800') and len(digits) in (9, 10):
        return True
    # أي دولي صالح (مصر، إمارات، كويت... إلخ)
    if p.startswith('+') and 10 <= len(digits) <= 15:
        return True
    return False


# ---------------------------------------------------------------------------
# 2) أنماط البحث عن الأرقام
# ---------------------------------------------------------------------------

SEP = r'[\s\-–—.()\[\]/\u200f\u200e]*'
PHONE_PATTERNS = [
    # صيغة السعودية مقسمة لمنع التقاط إحداثيات أو أرقام عشوائية
    r'(?<!\d)(?:\+?966|00966|0)' + SEP + r'5\d' + SEP + r'\d{3}' + SEP + r'\d{4}(?!\d)',
    r'(?<!\d)(?:\+?966|00966|0)' + SEP + r'5\d{8}(?!\d)',
    # أرضي سعودي
    r'(?<!\d)(?:\+?966|00966|0)' + SEP + r'1[1-7]' + SEP + r'\d{7}(?!\d)',
    # رقم مجاني أو موحد
    r'(?<!\d)9200' + SEP + r'\d{5}(?!\d)',
    r'(?<!\d)800' + SEP + r'\d{6,7}(?!\d)',
    # أي دولي بصيغة +
    r'(?<!\d)\+\d{1,4}' + SEP + r'(?:\d' + SEP + r'){7,13}\d(?!\d)',
]

# مفاتيح JSON/JS اللي المنصات بتخبي فيها الأرقام
JSON_PHONE_KEYS = (
    'phone', 'mobile', 'whatsapp', 'telephone', 'tel', 'contact_number',
    'support_phone', 'phone_number', 'call_us', 'hotline', 'contactPoint'
)


def extract_phones(raw_html: str, soup: BeautifulSoup) -> set:
    """بيدور في: الـ HTML الخام، النص المرئي (بطريقتين)، tel:، JSON configs."""
    found = set()

    def add(candidate):
        cp = clean_phone(candidate)
        if is_valid_phone(cp):
            found.add(cp)

    raw = normalize_digits(raw_html)

    # (أ) tel: و callto: و sms:
    for a in soup.find_all('a', href=True):
        href = normalize_digits(a['href'])
        if re.match(r'^(tel|callto|sms):', href, re.I):
            add(re.sub(r'^(tel|callto|sms):', '', href, flags=re.I))

    # (ب) attributes مخصصة
    SKIP_META = ('description', 'og:description', 'twitter:description', 'keywords')
    for attr in ('data-phone', 'data-tel', 'data-number', 'data-whatsapp', 'content'):
        for el in soup.find_all(attrs={attr: True}):
            if el.name == 'meta' and (el.get('name') or el.get('property') or '').lower() in SKIP_META:
                continue  # أرقام مخبأة في وصف الميتا غالباً غير ظاهرة للزوار
            val = normalize_digits(str(el.get(attr)))
            if re.search(r'\d{7,}', val):
                add(val)

    # (ج) مفاتيح JSON داخل السكريبتات (ده اللي كان ضايع)
    for key in JSON_PHONE_KEYS:
        for m in re.findall(r'"' + key + r'"\s*:\s*"([^"]{6,40})"', raw, re.I):
            add(m)

    # (د) النص المرئي — بطريقتين عشان منفوّتش أرقام مقسمة على تاجات
    soup_txt = BeautifulSoup(raw, 'html.parser')
    for el in soup_txt(["style", "noscript", "svg"]):
        el.extract()
    text_glued = soup_txt.get_text()            # أرقام مقسمة على <span>
    text_spaced = soup_txt.get_text(separator=' ')  # يمنع لزق أرقام مختلفة

    # (هـ) السكريبتات نفسها كنص خام
    scripts_text = " ".join(s.get_text() for s in soup_txt.find_all('script'))
    # أرقام مخبأة في حقول الوصف (JSON-LD description) غالباً غير ظاهرة للزوار
    scripts_text = re.sub(r'"(?:description|og:description|twitter:description|keywords)"\s*:\s*"(?:\\.|[^"\\])*"',
                          '', scripts_text, flags=re.I)

    for blob in (text_glued, text_spaced, scripts_text):
        for pat in PHONE_PATTERNS:
            for m in re.findall(pat, blob):
                add(m)

    return found


# ---------------------------------------------------------------------------
# 3) واتساب
# ---------------------------------------------------------------------------

WA_HOSTS = ('wa.me', 'api.whatsapp.com', 'web.whatsapp.com', 'whatsapp://', 'chat.whatsapp.com')


def extract_whatsapp(raw_html: str, phones: set) -> set:
    links = set()
    raw = normalize_digits(raw_html)

    for m in re.findall(r'https?://(?:api\.|web\.)?wa(?:\.me|tsapp\.com)[^\s"\'<>)]*', raw, re.I):
        if '${' in m or 'undefined' in m or 'PHONE' in m.upper():
            continue
        links.add(m.rstrip('/,.'))
    for m in re.findall(r'https?://chat\.whatsapp\.com/[A-Za-z0-9]+', raw):
        links.add(m)
    
    # استخراج رقم الواتساب إذا كان مخزناً كنص في JSON أو كـ mobile (مثل منصات سلة وتطبيقات BusinessChat)
    for m in re.findall(r'"(?:whatsapp|whats_app|whatsapp_number|mobile|phone)"\s*:\s*"([^"]{6,40})"', raw, re.I):
        cp = clean_phone(m)
        if is_valid_phone(cp):
            links.add(f"https://wa.me/{cp.lstrip('+')}")
            phones.add(cp)

    # استخراج الأرقام من داخل اللينكات (أي دولة مش السعودية بس)
    for link in list(links):
        num = None
        q = re.search(r'[?&]phone=(\+?\d{8,15})', link)
        if q:
            num = q.group(1)
        else:
            tail = re.search(r'wa\.me/(\+?\d{8,15})', link)
            if tail:
                num = tail.group(1)
        if num:
            cp = clean_phone(num)
            if is_valid_phone(cp):
                phones.add(cp)
                links.add(f"https://wa.me/{cp.lstrip('+')}")
    return links


# ---------------------------------------------------------------------------
# 4) السوشيال ميديا
# ---------------------------------------------------------------------------

SOCIAL_NETWORKS = {
    'فيسبوك':    (r'(?:facebook\.com|fb\.com|fb\.me)', ['sharer', 'share.php', '/plugins/', '/tr?', '/dialog/', 'connect.facebook']),
    'انستجرام':  (r'instagram\.com',                   ['/p/', '/reel', '/explore', '/stories/', '/embed']),
    'تيك توك':   (r'tiktok\.com',                      ['/embed', '/music/', '/discover']),
    'تويتر / X': (r'(?:twitter\.com|x\.com)',          ['/intent/', '/share', '/hashtag/', '/search', '/home']),
    'سناب شات':  (r'snapchat\.com',                    ['/creator', '/discover']),
    'يوتيوب':    (r'(?:youtube\.com|youtu\.be)',       ['/watch', '/embed', '/results']),
    'لينكدإن':   (r'linkedin\.com',                    ['/share', '/sharing', '/shareArticle']),
    'تيليجرام':  (r'(?:t\.me|telegram\.me)',           ['/share']),
    'بنترست':    (r'pinterest\.com',                   ['/pin/', '/pin-builder', '/create']),
}

GENERIC_JUNK = ('salla.sa', 'zid.sa', 'schema.org', 'w3.org', 'widgets', 'googleapis',
                'example.com', 'yourstore', '${', 'undefined', '{{')


def _normalize_social(url: str) -> str:
    url = htmllib.unescape(url.strip()).rstrip('/,.')
    if url.startswith('//'):
        url = 'https:' + url
    parts = urllib.parse.urlsplit(url)
    # نشيل تراكينج بس
    query = urllib.parse.urlencode([
        (k, v) for k, v in urllib.parse.parse_qsl(parts.query)
        if not k.lower().startswith(('utm_', 'fbclid', 'igshid', 'ref'))
    ])
    path = parts.path.rstrip('/')
    return urllib.parse.urlunsplit(('https', parts.netloc.lower().replace('www.', ''), path, query, ''))


def extract_socials(raw_html: str, soup: BeautifulSoup) -> dict:
    """بيدور في الـ HTML الخام كله — a tags، JSON-LD sameAs، meta، وسكريبتات."""
    results = {k: set() for k in SOCIAL_NETWORKS}
    raw = htmllib.unescape(raw_html).replace(r'\/', '/')

    # البحث الشامل بالريجكس في أي مكان في الصفحة
    candidates = set(re.findall(r'https?://[^\s"\'<>)\\]{6,200}', raw))
    candidates |= {a['href'] for a in soup.find_all('a', href=True)}
    for tag in soup.find_all('meta', attrs={'content': True}):
        if 'http' in tag['content']:
            candidates.add(tag['content'])

    # JSON-LD sameAs
    for script in soup.find_all('script', type=lambda t: t and 'ld+json' in t):
        try:
            data = json.loads(script.string or '{}')
        except Exception:
            continue
        for blob in (data if isinstance(data, list) else [data]):
            if isinstance(blob, dict):
                same = blob.get('sameAs') or []
                candidates |= set(same if isinstance(same, list) else [same])

    for link in candidates:
        low = link.lower()
        if any(j in low for j in GENERIC_JUNK):
            continue
        for network, (pattern, blacklist) in SOCIAL_NETWORKS.items():
            if re.search(pattern, low) and not any(b in low for b in blacklist):
                clean = _normalize_social(link)
                # لازم يكون فيه يوزرنيم مش دومين لوحده
                if len(urllib.parse.urlsplit(clean).path.strip('/')) >= 2:
                    results[network].add(clean)
    return results


# ---------------------------------------------------------------------------
# 5) الإيميلات (مع فك تشفير Cloudflare والتمويه)
# ---------------------------------------------------------------------------

EMAIL_RE = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
BAD_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js', '.woff', '.ttf', '.mp4')


def _decode_cfemail(encoded: str) -> str:
    try:
        r = int(encoded[:2], 16)
        return ''.join(chr(int(encoded[i:i + 2], 16) ^ r) for i in range(2, len(encoded), 2))
    except Exception:
        return ''


def extract_emails(raw_html: str, soup: BeautifulSoup) -> set:
    emails = set()
    raw = htmllib.unescape(raw_html)

    for a in soup.find_all('a', href=True):
        if a['href'].lower().startswith('mailto:'):
            emails.add(a['href'][7:].split('?')[0].strip())

    # Cloudflare email protection
    for el in soup.find_all(attrs={'data-cfemail': True}):
        dec = _decode_cfemail(el['data-cfemail'])
        if '@' in dec:
            emails.add(dec)

    # تمويه نصي: info [at] site [dot] com
    visible_text = soup.get_text(separator=' ')
    deobf = re.sub(r'\s*[\[\(]?\s*\b(at|أت)\b\s*[\]\)]?\s*', '@', visible_text, flags=re.I)
    deobf = re.sub(r'\s*[\[\(]?\s*\b(dot|نقطة)\b\s*[\]\)]?\s*', '.', deobf, flags=re.I)

    for blob in (raw, deobf):
        for em in re.findall(EMAIL_RE, blob):
            low = em.lower()
            if low.endswith(BAD_EXT):
                continue
            if any(p in low for p in ('salla.sa', 'zid.sa', 'schema.org', 'w3.org', 'example.com', 'domain.com', 'yourstore')):
                continue
            if re.search(r'\.{2,}|@.*@|^(test|admin|example|fake|email|user|name)@|sentry|wixpress|\.wp\.com', low):
                continue
            emails.add(em.strip('.'))
    return emails


# ---------------------------------------------------------------------------
# 6) اكتشاف الصفحات الداخلية المهمة
# ---------------------------------------------------------------------------

PAGE_KEYWORDS = ['contact', 'about', 'اتصل', 'تواصل', 'من-نحن', 'عن-المتجر', 'help',
                 'support', 'faq', 'الأسئلة', 'policies', 'الشروط', 'privacy', 'من نحن']

FALLBACK_PATHS = ['/contact-us', '/contact', '/pages/contact-us', '/ar/contact-us',
                  '/about-us', '/pages/about-us', '/اتصل-بنا', '/تواصل-معنا']


def discover_pages(soup: BeautifulSoup, domain: str, limit: int = 5) -> list:
    urls, seen = [], set()

    def push(u):
        u = u.split('#')[0].rstrip('/')
        if u and u not in seen:
            seen.add(u)
            urls.append(u)

    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        label = (a.get_text() or '') + ' ' + href
        if any(k in label.lower() for k in PAGE_KEYWORDS):
            if href.startswith('/'):
                push(f"https://{domain}{href}")
            elif href.startswith('http') and domain in href:
                push(href)

    for p in FALLBACK_PATHS:
        push(f"https://{domain}{p}")

    return urls[:limit]


# ---------------------------------------------------------------------------
# 7) الدالة الرئيسية — تجمع كل حاجة من كل الصفحات
# ---------------------------------------------------------------------------

def harvest_domain(domain: str, fetch_url, max_pages: int = 3) -> dict:
    """
    fetch_url: دالة ترجع response أو None.
    تجمع كل البيانات من الصفحة الرئيسية + الصفحات الداخلية (اتصل بنا / من نحن).
    """
    bucket = {
        'phones': set(), 'whatsapp': set(), 'emails': set(),
        'socials': {k: set() for k in SOCIAL_NETWORKS},
        'title': '', 'platform': 'غير معروف', 'active': False,
    }

    candidates = (
        f"https://{domain}",
        f"https://www.{domain}",
        f"https://{domain}/ar",
        f"http://{domain}"
    )

    res = None
    for url in candidates:
        r = fetch_url(url)
        if r is not None and getattr(r, 'status_code', None) == 200:
            res = r
            break

    if res is None:
        return bucket

    bucket['active'] = True
    home_html = res.text
    home_soup = BeautifulSoup(home_html, 'html.parser')

    t = home_soup.find('title')
    if t:
        bucket['title'] = t.get_text(strip=True)

    low = home_html.lower()
    if any(k in low for k in ('salla.sa', 'twilight', 'salla-', 's.salla')):
        bucket['platform'] = 'سلة (Salla)'
    elif any(k in low for k in ('zid.sa', 'zid-store', 'media.zid')):
        bucket['platform'] = 'زد (Zid)'
    elif 'shopify' in low:
        bucket['platform'] = 'Shopify'
    elif 'woocommerce' in low or 'wp-content' in low:
        bucket['platform'] = 'WooCommerce/WP'

    def absorb(html_str):
        soup = BeautifulSoup(html_str, 'html.parser')
        bucket['phones'] |= extract_phones(html_str, soup)
        bucket['whatsapp'] |= extract_whatsapp(html_str, bucket['phones'])
        bucket['emails'] |= extract_emails(html_str, soup)
        for net, links in extract_socials(html_str, soup).items():
            bucket['socials'][net] |= links
        return soup

    absorb(home_html)

    # جلب الصفحات الداخلية المهمة تسلسلياً (اتصل بنا / من نحن)
    inner_urls = discover_pages(home_soup, domain, limit=max_pages)
    for page_url in inner_urls:
        page = fetch_url(page_url)
        if page is not None and getattr(page, 'status_code', None) == 200:
            absorb(page.text)

    return bucket


def bucket_to_row(domain: str, bucket: dict) -> dict:
    """يحوّل النتيجة لصف جاهز للـ DataFrame."""
    join = lambda s: " | ".join(sorted(s))
    row = {
        'الموقع (Domain)': domain,
        'عنوان المتجر': bucket['title'],
        'منصة المتجر': bucket['platform'],
        'الحالة': 'نشط' if bucket['active'] else 'غير متاح',
        'أرقام التواصل': join(bucket['phones']),
        'عدد الأرقام': len(bucket['phones']),
        'رابط الواتساب': join(bucket['whatsapp']),
        'البريد الإلكتروني': join(bucket['emails']),
    }
    for net in SOCIAL_NETWORKS:
        row[net] = join(bucket['socials'][net])
    return row
