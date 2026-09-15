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
from extractors import harvest_domain, bucket_to_row, SOCIAL_NETWORKS

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
    @import url('https://fonts.googleapis.com/css2?family=Calistoga&family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Readex+Pro:wght@200;300;400;500;600;700&display=swap');

    :root {
        --bg: #070A12;
        --surface: rgba(255,255,255,0.045);
        --surface-2: rgba(255,255,255,0.075);
        --border: rgba(255,255,255,0.09);
        --fg: #F1F5F9;
        --muted: #8D9BB5;
        --a1: #2F6BFF;
        --a2: #6D5DFF;
        --a3: #22D3EE;
        --grad: linear-gradient(120deg, #2F6BFF 0%, #6D5DFF 45%, #22D3EE 100%);
        --radius: 22px;
    }

    html, body, [class*="css"], .stApp, .stMarkdown, p, div, h1,h2,h3,h4,h5,h6, label, span {
        font-family: 'Readex Pro','Inter',-apple-system,sans-serif;
        direction: rtl !important;
        text-align: right !important;
        color: var(--fg);
    }

    /* ===== خلفية Aurora متحركة + حبيبات ناعمة ===== */
    .stApp {
        background:
          radial-gradient(60rem 40rem at 15% -10%, rgba(47,107,255,.28), transparent 60%),
          radial-gradient(50rem 35rem at 95% 0%, rgba(109,93,255,.22), transparent 60%),
          radial-gradient(45rem 30rem at 50% 110%, rgba(34,211,238,.16), transparent 60%),
          var(--bg) !important;
        background-attachment: fixed !important;
    }
    .stApp::before {
        content:""; position:fixed; inset:0; pointer-events:none; opacity:.035; z-index:0;
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    }
    .stApp > header { background: transparent !important; }
    [data-testid="stSidebar"] {
        background: rgba(10,14,24,.75) !important;
        backdrop-filter: blur(18px);
        border-left: 1px solid var(--border);
    }
    ::-webkit-scrollbar { width: 9px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,.14); border-radius: 9px; }

    [data-testid="column"] { direction: rtl !important; }
    .hero-headline, .hero-sub, .min-card, .min-card h3, .min-card p, .stButton>button { text-align:center !important; }

    /* ===== البادج ===== */
    .badge-container { display:flex; justify-content:center; width:100%; margin: 6px 0 18px; }
    .section-badge {
        display:inline-flex; align-items:center; gap:10px;
        background: rgba(255,255,255,.05);
        border: 1px solid var(--border);
        backdrop-filter: blur(12px);
        padding: 7px 18px; border-radius: 9999px; direction: ltr !important;
    }
    .badge-dot {
        width:8px; height:8px; border-radius:50%; background: var(--a3);
        box-shadow: 0 0 14px var(--a3); animation: pulse 2.2s infinite ease-in-out;
    }
    @keyframes pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.5);opacity:.5} }
    .badge-text {
        font-family:'JetBrains Mono',monospace; font-size:11.5px; font-weight:600;
        letter-spacing:.18em; color:#CBD5E1; text-transform:uppercase; margin:0 !important;
    }

    /* ===== العنوان الرئيسي ===== */
    .hero-headline {
        font-family:'Calistoga','Readex Pro',serif !important;
        font-size: clamp(34px, 5.2vw, 62px);
        line-height: 1.45 !important; letter-spacing:-.02em; margin-bottom:18px;
    }
    .gradient-text {
        background: var(--grad); background-size: 220% auto;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        display:inline-block; animation: shine 6s linear infinite;
    }
    @keyframes shine { to { background-position: 220% center; } }
    .hero-sub {
        font-size:17px; font-weight:300; color: var(--muted);
        max-width: 660px; line-height:1.9; margin: 0 auto 38px auto;
    }

    /* ===== كروت زجاجية بحافة متدرجة ===== */
    .min-card {
        position: relative; background: var(--surface);
        border: 1px solid var(--border); border-radius: var(--radius);
        padding: 30px 22px; backdrop-filter: blur(16px);
        transition: all .35s cubic-bezier(.16,1,.3,1); overflow: hidden;
    }
    .min-card::after {
        content:""; position:absolute; inset:0; border-radius: var(--radius);
        padding:1px; background: var(--grad); opacity:0;
        -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
        -webkit-mask-composite: xor; mask-composite: exclude;
        transition: opacity .35s ease;
    }
    .min-card:hover { transform: translateY(-6px); background: var(--surface-2); }
    .min-card:hover::after { opacity:1; }
    .min-card h3 {
        font-family:'Calistoga',serif !important; font-size:32px !important; margin:0 0 6px !important;
        background: var(--grad); -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    }
    .min-card p { font-size:14px; color: var(--muted); font-weight:300; margin:0; }

    /* ===== زرار فيه لمعة بتمر ===== */
    .stButton { display:flex; justify-content:center; margin:14px 0 22px; }
    .stButton>button {
        position: relative; overflow: hidden;
        background: var(--grad) !important; background-size:200% auto !important;
        color:#fff !important; font-family:'Readex Pro',sans-serif !important;
        font-size:17px !important; font-weight:600 !important;
        border-radius:16px !important; padding:15px 40px !important; border:none !important;
        box-shadow: 0 10px 34px rgba(47,107,255,.38) !important;
        transition: all .3s cubic-bezier(.16,1,.3,1) !important;
    }
    .stButton>button::before {
        content:""; position:absolute; top:0; left:-120%; width:60%; height:100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,.35), transparent);
        animation: sweep 3.2s infinite;
    }
    @keyframes sweep { 0%{left:-120%} 60%,100%{left:140%} }
    .stButton>button:hover {
        transform: translateY(-3px) !important; background-position: right center !important;
        box-shadow: 0 16px 44px rgba(109,93,255,.5) !important;
    }
    .stButton>button:active { transform: scale(.98) !important; }

    /* ===== تابات على شكل Segmented Pills ===== */
    [data-baseweb="tab-list"] {
        gap:8px; border-bottom:none !important;
        background: var(--surface); border:1px solid var(--border);
        padding:6px; border-radius:16px; backdrop-filter: blur(12px);
        width: fit-content; margin: 0 auto 22px auto;
        justify-content:center !important; flex-direction: row !important;
    }
    [data-baseweb="tab"] {
        font-family:'Readex Pro',sans-serif !important; font-size:15px !important; font-weight:500 !important;
        border-radius:12px !important; padding: 9px 20px !important; color: var(--muted) !important;
        transition: all .25s ease;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background: var(--grad) !important; color:#fff !important;
        box-shadow: 0 6px 18px rgba(47,107,255,.35);
    }
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display:none !important; }

    /* ===== الرفع والإدخال ===== */
    div[data-testid="stFileUploader"] {
        background: var(--surface) !important;
        border: 1.5px dashed rgba(109,93,255,.45) !important;
        border-radius:18px !important; padding:34px !important;
        backdrop-filter: blur(12px); transition: all .3s ease !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: var(--a3) !important; background: var(--surface-2) !important;
    }
    .stTextArea textarea {
        background: var(--surface) !important; color: var(--fg) !important;
        border:1px solid var(--border) !important; border-radius:16px !important;
        padding:16px !important; font-family:'Readex Pro',sans-serif !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--a1) !important; box-shadow: 0 0 0 3px rgba(47,107,255,.18) !important;
    }

    /* ===== سيكشن النتائج المقلوب ===== */
    .inverted-section {
        background: linear-gradient(135deg, rgba(47,107,255,.16), rgba(109,93,255,.10));
        border:1px solid var(--border); backdrop-filter: blur(18px);
        border-radius:24px; padding:30px; margin-top:28px;
        box-shadow: 0 24px 60px rgba(0,0,0,.45); text-align:right;
    }

    /* ===== الجدول والبروجريس ===== */
    [data-testid="stDataFrame"] {
        direction: rtl !important; border:1px solid var(--border);
        border-radius:16px; overflow:hidden;
    }
    .stProgress > div > div > div > div { background: var(--grad) !important; }
    [data-testid="stDownloadButton"] button {
        background: var(--surface-2) !important; border:1px solid var(--border) !important;
        color: var(--fg) !important; border-radius:14px !important; padding:12px 26px !important;
    }
    [data-testid="stDownloadButton"] button:hover { border-color: var(--a3) !important; }

    #MainMenu, footer, [data-testid="stDecoration"] { visibility:hidden; }
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

def fetch_url(url, retries=1):
    for attempt in range(retries):
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        try:
            res = requests.get(url, headers=headers, timeout=6,
                               allow_redirects=True, verify=False)
            if res is not None and len(res.text) > 300:
                return res
        except Exception:
            pass
    return None

def scrape_single_domain(domain):
    domain = domain.strip().replace('https://', '').replace('http://', '').split('/')[0]
    bucket = harvest_domain(domain, fetch_url, max_pages=5)
    row = bucket_to_row(domain, bucket)

    rank = get_tranco_rank(domain) if bucket['active'] else None
    visits, est_rev, _ = estimate_metrics(rank, row['منصة المتجر'], bucket['active'])
    row['الزيارات الشهرية التقديرية'] = f"{visits:,}"
    row['العوائد الشهرية التقديرية (SAR)'] = est_rev
    return row

# --- MINIMALIST MODERN HERO SECTION ---
st.markdown("""
<div class="badge-container">
  <div class="section-badge">
    <div class="badge-dot"></div>
    <div class="badge-text">Automated Intelligence Platform</div>
  </div>
</div>
<div class="hero-headline">
    استخراج بيانات المتاجر<br><span class="gradient-text">بدقة مطلقة وهيكلة ذكية</span>
</div>
<div class="hero-sub">
    منصة تعتمد على الاستخراج المتوازي لوسائل التواصل، الأرقام المخبأة داخل كود المتجر،
    وتقديرات الترافيك والعوائد الشهرية — في ثوانٍ.
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
        status_text.info("⏳ جاري تحضير المحركات والبدء في الفحص... يرجى الانتظار (قد يستغرق فحص الموقع الأول بضع ثوانٍ)")
        
        results = []
        total = len(domain_list)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
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
