import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment
import re
import urllib.parse
import json
import concurrent.futures
import time
import random
import io
import openpyxl
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(
    page_title="Scraper Pro — Minimalist Modern",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# MINIMALIST MODERN DESIGN SYSTEM STYLES (Design Tokens & Philosophy Injected)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Calistoga&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Readex+Pro:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-main: #FAFAFA;
        --fg-main: #0F172A;
        --muted-bg: #F1F5F9;
        --muted-fg: #64748B;
        --accent-start: #0052FF;
        --accent-end: #4D7CFF;
        --accent-gradient: linear-gradient(135deg, #0052FF 0%, #4D7CFF 100%);
        --card-bg: #FFFFFF;
        --border-color: #E2E8F0;
        --dark-card: #1E293B;
    }
    
    /* Enforce robust RTL & Base Typography */
    html, body, [class*="css"], .stApp, .stMarkdown, p, div, h1, h2, h3, h4, h5, h6, label {
        font-family: 'Readex Pro', 'Inter', -apple-system, sans-serif;
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Background Override */
    .stApp, .stApp > header {
        background-color: var(--bg-main) !important;
    }
    
    /* Ensure layout columns stay proper in RTL */
    [data-testid="column"] {
        direction: rtl !important;
    }
    
    /* Center Specific UI Elements */
    .hero-headline, .hero-sub, .min-card, .min-card h3, .min-card p, .stButton>button {
        text-align: center !important;
    }
    
    /* Center the badge container itself */
    .badge-container {
        display: flex;
        justify-content: center;
        width: 100%;
        margin-bottom: 16px;
    }

    /* Section Badge System */
    .section-badge {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        background: rgba(0, 82, 255, 0.06);
        border: 1px solid rgba(0, 82, 255, 0.25);
        padding: 6px 18px;
        border-radius: 9999px;
        direction: ltr !important; /* Keep badge text LTR */
    }
    .badge-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: var(--accent-start);
        box-shadow: 0 0 10px var(--accent-start);
        animation: pulse 2s infinite ease-in-out;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.4); opacity: 0.6; }
    }
    .badge-text {
        font-family: 'JetBrains Mono', 'Readex Pro', monospace;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.12em;
        color: var(--accent-start);
        text-transform: uppercase;
        margin-bottom: 0 !important;
    }
    
    /* Display Headline with Signature Gradient Text */
    .hero-headline {
        font-family: 'Calistoga', 'Readex Pro', serif !important;
        font-size: 52px;
        font-weight: 700;
        line-height: 1.6 !important; /* Increased line spacing */
        color: var(--fg-main);
        margin-bottom: 20px;
        letter-spacing: -0.01em;
    }
    .gradient-text {
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }
    .hero-sub {
        font-size: 18px;
        color: var(--muted-fg);
        max-width: 680px;
        line-height: 1.8;
        margin: 0 auto 40px auto;
    }
    
    /* Cards with Elevated Layered Shadows & Precise Borders */
    .min-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        padding: 28px 24px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .min-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0, 82, 255, 0.12);
        border-color: rgba(0, 82, 255, 0.3);
    }
    .min-card h3 {
        font-family: 'Calistoga', 'Readex Pro', serif !important;
        font-size: 34px !important;
        margin: 0 0 8px 0 !important;
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .min-card p {
        font-size: 15px;
        color: var(--muted-fg);
        margin: 0;
        font-weight: 500;
    }
    
    /* Signature Electric Blue Gradient Action Buttons */
    .stButton {
        display: flex;
        justify-content: center;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .stButton>button {
        background: var(--accent-gradient) !important;
        color: #FFFFFF !important;
        font-family: 'Readex Pro', sans-serif !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        border-radius: 14px !important;
        padding: 14px 36px !important;
        border: none !important;
        box-shadow: 0 6px 20px rgba(0, 82, 255, 0.3) !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 28px rgba(0, 82, 255, 0.45) !important;
        filter: brightness(1.05);
    }
    .stButton>button:active {
        transform: scale(0.98) !important;
    }
    
    /* Tabs Styling */
    [data-baseweb="tab-list"] {
        gap: 16px;
        border-bottom: 2px solid var(--border-color);
        justify-content: flex-start !important;
        flex-direction: row !important;
    }
    [data-baseweb="tab"] {
        font-family: 'Readex Pro', sans-serif !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding-top: 12px;
        padding-bottom: 12px;
    }
    
    /* Inverted Slate Container Strategy */
    .inverted-section {
        background-color: var(--fg-main);
        background-image: radial-gradient(circle, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
        background-size: 24px 24px;
        color: #FFFFFF !important;
        border-radius: 24px;
        padding: 32px;
        margin-top: 32px;
        box-shadow: 0 20px 40px rgba(15, 23, 42, 0.15);
        text-align: right;
    }
    .inverted-section h3, .inverted-section p {
        color: #FFFFFF !important;
        text-align: right !important;
    }
    
    /* Custom Inputs & Dropzone */
    div[data-testid="stFileUploader"] {
        background: #FFFFFF !important;
        border: 2px dashed rgba(0, 82, 255, 0.3) !important;
        border-radius: 16px !important;
        padding: 32px !important;
        transition: border-color 0.25s ease !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: var(--accent-start) !important;
        background: rgba(0, 82, 255, 0.01) !important;
    }
    
    /* Text Area */
    .stTextArea textarea {
        background: #FFFFFF !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 14px !important;
        font-family: 'Readex Pro', sans-serif !important;
        padding: 16px !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--accent-start) !important;
        box-shadow: 0 0 0 1px var(--accent-start) !important;
    }
    
    /* Dataframe Header RTL Fixes */
    [data-testid="stDataFrame"] {
        direction: rtl !important;
    }
    
    /* Hide Streamlit Default UI Clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
]

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
        res = requests.get(url, headers=headers, timeout=8, allow_redirects=True, verify=False)
        if res and len(res.text) > 300:
            return res
    except Exception:
        pass
    return None

def scrape_single_domain(domain):
    domain = domain.strip().replace('https://', '').replace('http://', '').split('/')[0]
    item = {
        'الموقع (Domain)': domain,
        'عنوان المتجر': '',
        'منصة المتجر': 'غير معروف',
        'الحالة': 'غير متاح',
        'أرقام التواصل': '',
        'رابط الواتساب': '',
        'البريد الإلكتروني': '',
        'فيسبوك': '',
        'انستجرام': '',
        'تيك توك': '',
        'تويتر / X': '',
        'سناب شات': '',
        'الزيارات الشهرية التقديرية': '0',
        'العوائد الشهرية التقديرية (SAR)': '0 SAR'
    }

    res = None
    target_urls = [f"https://{domain}/ar", f"https://www.{domain}/ar", f"https://{domain}", f"https://www.{domain}"]
    for url in target_urls:
        res = fetch_url(url)
        if res and res.status_code == 200:
            break

    if not res:
        return item

    html_content = res.text
    soup = BeautifulSoup(html_content, 'html.parser')
    item['الحالة'] = 'نشط'

    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        item['عنوان المتجر'] = title_tag.string.strip()

    page_text_lower = html_content.lower()
    if 'salla.sa' in page_text_lower or 'cdn.salla.sa' in page_text_lower or 'twilight' in page_text_lower:
        item['منصة المتجر'] = 'سلة (Salla)'
    elif 'zid.sa' in page_text_lower or 'cdn.zid.sa' in page_text_lower or 'zid-store' in page_text_lower:
        item['منصة المتجر'] = 'زد (Zid)'
    elif 'shopify' in page_text_lower:
        item['منصة المتجر'] = 'Shopify'
    elif 'wp-content' in page_text_lower or 'woocommerce' in page_text_lower:
        item['منصة المتجر'] = 'WooCommerce/WP'

    phones = set()
    whatsapp_links = set()

    wa_json = re.findall(r'"whatsapp":\s*"([^"]+)"', html_content, re.IGNORECASE)
    phone_json = re.findall(r'"phone":\s*"([^"]+)"|"mobile":\s*"([^"]+)"', html_content, re.IGNORECASE)

    for w in wa_json:
        if w.strip():
            cp = clean_phone(w.strip())
            if is_valid_phone(cp):
                phones.add(cp)
                whatsapp_links.add(f"https://wa.me/{cp.replace('+', '')}")

    for p_tuple in phone_json:
        for p in p_tuple:
            if p.strip():
                cp = clean_phone(p.strip())
                if is_valid_phone(cp):
                    phones.add(cp)

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

    soup_clean = BeautifulSoup(html_content, 'html.parser')
    for element in soup_clean(["script", "style", "head", "noscript"]):
        element.extract()
    visible_text = soup_clean.get_text()

    raw_mobiles = re.findall(r'(?:\+?966|00966|0)?5\d{8,9}\b', visible_text)
    raw_unified = re.findall(r'\b9200\d{5}\b', visible_text)
    raw_tollfree = re.findall(r'\b800\d{6,7}\b', visible_text)

    for p in raw_mobiles + raw_unified + raw_tollfree:
        cp = clean_phone(p)
        if is_valid_phone(cp):
            phones.add(cp)

    emails = set()
    for link in links:
        if link.startswith('mailto:'):
            emails.add(link.replace('mailto:', '').split('?')[0].strip())
    email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', visible_text)
    for em in email_matches:
        if not em.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js', '.woff', '.ttf')):
            emails.add(em)

    social_map = {
        'فيسبوك': ['facebook.com', 'fb.com'],
        'انستجرام': ['instagram.com'],
        'تيك توك': ['tiktok.com'],
        'تويتر / X': ['twitter.com', 'x.com'],
        'سناب شات': ['snapchat.com']
    }
    found_socials = {k: set() for k in social_map}
    for link in links:
        l_lower = link.lower()
        for platform, domains in social_map.items():
            if any(d in l_lower for d in domains):
                if not any(x in l_lower for x in ['share', 'intent/tweet', 'sharer.php', 'salla.sa', 'widgets', 'schema.org']):
                    found_socials[platform].add(link)

    rank = get_tranco_rank(domain)
    visits, est_rev, _ = estimate_metrics(rank, item['منصة المتجر'], True)

    item['أرقام التواصل'] = " | ".join(sorted(list(phones)))
    item['رابط الواتساب'] = " | ".join(sorted(list(whatsapp_links)))
    item['البريد الإلكتروني'] = " | ".join(sorted(list(emails)))
    item['فيسبوك'] = " | ".join(sorted(list(found_socials['فيسبوك'])))
    item['انستجرام'] = " | ".join(sorted(list(found_socials['انستجرام'])))
    item['تيك توك'] = " | ".join(sorted(list(found_socials['تيك توك'])))
    item['تويتر / X'] = " | ".join(sorted(list(found_socials['تويتر / X'])))
    item['سناب شات'] = " | ".join(sorted(list(found_socials['سناب شات'])))
    item['الزيارات الشهرية التقديرية'] = f"{visits:,}"
    item['العوائد الشهرية التقديرية (SAR)'] = est_rev

    return item

# --- MINIMALIST MODERN HERO SECTION ---
st.markdown("""
<div class="badge-container">
    <div class="section-badge">
        <div class="badge-dot"></div>
        <div class="badge-text">AUTOMATED INTELLIGENCE PLATFORM</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-headline">
    استخراج بيانات المتاجر <br><span class="gradient-text">بدقة مطلقة وهيكلة ذكية</span>
</div>
<div class="hero-sub">
    منصة حديثة تعتمد على البنية الدقيقة للاستخراج المتوازي لوسائل التواصل، أرقام السلات المخبأة، وتقديرات الترافيك والعوائد الشهرية.
</div>
""", unsafe_allow_html=True)

# Metric Feature Cards
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="min-card"><h3>100%</h3><p>دقة السحب البرمجي (Salla JSON)</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="min-card"><h3>Multi-Thread</h3><p>فحص متوازي لـ 100+ موقع في ثوانٍ</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="min-card"><h3>Instant Export</h3><p>تصدير مهيكل لملفات Excel و CSV</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Container Tabs
tab1, tab2 = st.tabs(["📁 رفع ملف Excel / CSV", "📝 إدخال روابط يدوياً"])

domain_list = []

with tab1:
    uploaded_file = st.file_uploader("قم بسحب وإسقاط ملف Excel أو CSV يحتوي على الروابط:", type=["xlsx", "csv", "xls"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_in = pd.read_csv(uploaded_file)
            else:
                df_in = pd.read_excel(uploaded_file)
            
            first_col = df_in.iloc[:, 0].dropna().astype(str).tolist()
            domain_list = [d.strip() for d in first_col if d.strip()]
            st.success(f"✓ تم تجهيز {len(domain_list)} موقع للبدء الفوري")
        except Exception as e:
            st.error(f"خطأ في قراءة الملف: {e}")

with tab2:
    text_input = st.text_area("أدخل قائمة الروابط (رابط في كل سطر):", height=150, placeholder="villagemarket.com.sa\nmathaqshafi.com\nwtr.sa")
    if text_input:
        lines = text_input.splitlines()
        domain_list = [l.strip() for l in lines if l.strip()]

if domain_list:
    st.markdown(f"### ⚙️ الروابط المجهزة للبدء: **{len(domain_list)} موقع**")
    if st.button("🚀 بدء الاستخراج التلقائي الان"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        total = len(domain_list)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(scrape_single_domain, dom): dom for dom in domain_list}
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                results.append(res)
                completed += 1
                progress_bar.progress(completed / total)
                status_text.markdown(f"**جاري فحص وتدقيق ({completed}/{total}) موقع...**")
                
        st.balloons()
        st.success("🎉 اكتمل فحص واكتشاف جميع المواقع بنجاح!")
        
        df_res = pd.DataFrame(results)
        
        # Display Inverted Summary Card
        st.markdown(f"""
        <div class="inverted-section">
            <h3 style="font-family:'Calistoga',serif; font-size:28px; margin-bottom:8px;">إحصائيات الفحص النهائي</h3>
            <p style="color:#94A3B8; margin-bottom:16px;">تم فحص {len(df_res)} موقع بنجاح مئة بالمئة بنظام الفلترة الدقيق.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df_res, width='stretch')
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_res.to_excel(writer, index=False, sheet_name='البيانات المستخرجة')
        buffer.seek(0)
        
        st.download_button(
            label="📥 تحميل ملف Excel النهائي والمهيكل",
            data=buffer,
            file_name="scraped_contacts_and_metrics_minimalist.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
