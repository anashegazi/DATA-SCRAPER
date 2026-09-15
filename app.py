import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment
import re
import urllib.parse
import json
import concurrent.futures
import random
import io
import os
import threading
import openpyxl
import urllib3
from extractors import harvest_domain, bucket_to_row, SOCIAL_NETWORKS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# Resume persistence — النتائج بتتحفظ على القرص وباينة حتى بعد موت الـ process
# ---------------------------------------------------------------------------
RESULTS_FILE = 'partial_results.jsonl'
_lock = threading.Lock()

# ── ضبط سرعة وأداء الفحص ──
CHUNK_SIZE = 25        # عدد الدومينات في كل دفعة
MAX_WORKERS = 15       # عدد العمال المتزامنين
REQUEST_TIMEOUT = (2.5, 3.5)  # مهلة الطلب (اتصال 2.5 ثانية، قراءة 3.5 ثانية)

def _save_row(row):
    with _lock:
        with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

def _load_done():
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

# ---------------------------------------------------------------------------
# Thread-local Session — reuse اتصال واحد لكل thread بدل فتح واحد جديد لكل request
# ---------------------------------------------------------------------------
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
        return 0, "0 SAR", "غير نشط"
        
    if tranco_rank and tranco_rank > 0:
        monthly_visits = int(100_000_000_000 / (tranco_rank ** 1.12))
        monthly_visits = max(monthly_visits, 800)
    else:
        # مواقع خارج تصنيف Tranco (صغيرة جداً أو جديدة)
        base = 800 if any(p in platform for p in ['Salla', 'Zid', 'Shopify', 'WooCommerce', 'سلة', 'زد']) else 300
        # نضيف القليل من العشوائية حتى لا تبدو الأرقام كلها ثابتة
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
    session = _get_session()
    for attempt in range(retries):
        try:
            res = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            if res is None:
                continue
            # fast-fail: Cloudflare challenge → مفيش داعي نجرب باقي الصيغ
            if res.status_code in (403, 429, 503):
                server = (res.headers.get('Server') or '').lower()
                cfm = (res.headers.get('cf-mitigated') or '').lower()
                head = (res.text or '')[:300]
                if 'cloudflare' in server or cfm == 'yes' or 'just a moment' in head.lower():
                    return None
            if len(res.text) > 300:
                return res
        except Exception:
            pass
    return None




def scrape_single_domain(domain, fast=False):
    try:
        domain = domain.strip().replace('https://', '').replace('http://', '').split('/')[0].strip()
        if not domain:
            return error_row(domain)
        # fast: الرئيسية بس — الكامل: homepage + الداخلية
        bucket = harvest_domain(domain, fetch_url, max_pages=0 if fast else 5)
        row = bucket_to_row(domain, bucket)
        # الأعمدة موجودة وفارغة ليتم ملؤها يدوياً
        row['الزيارات الشهرية التقديرية'] = ''
        row['العوائد الشهرية التقديرية (SAR)'] = ''
        return row
    except Exception:
        return error_row(domain)


def error_row(domain):
    """صف بأعمدة متطابقة مع النجاح — عشان دومين واحد مشيميش shutdown ولا يطيح الدفعة كلها."""
    bucket = {
        'phones': set(), 'whatsapp': set(), 'emails': set(),
        'socials': {k: set() for k in SOCIAL_NETWORKS},
        'title': '', 'platform': 'غير معروف', 'active': False,
    }
    row = bucket_to_row(domain, bucket)
    row['الزيارات الشهرية التقديرية'] = ''
    row['العوائد الشهرية التقديرية (SAR)'] = ''
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
    domain_list = [d.strip() for d in domain_list if d and d.strip()]
    total = len(domain_list)

    # ── حالة الجلسة: تعيش عبر الـ reruns وتتوهج عند إعادة فتح المتصفح ──
    if "domains_queue" not in st.session_state:
        st.session_state.domains_queue = []
        st.session_state.done_domains = set()
        st.session_state.fast_mode = True
        st.session_state.scan_started = False

    scan_mode = st.radio(
        "⚡ نوع الفحص:",
        [
            "سريع — الصفحة الرئيسية فقط (فائق السرعة)",
            "شامل — الرئيسية + صفحات التواصل (اتصل بنا / من نحن)",
        ],
        horizontal=True,
    )
    st.session_state.fast_mode = scan_mode.startswith("سريع")

    st.markdown(f"### ⚙️ الروابط الجاهزة: **{total} موقع**")

    if st.button("🚀 بدء الاستخراج التلقائي الآن"):
        st.session_state.domains_queue = list(domain_list)
        st.session_state.done_domains = {r.get('الموقع (Domain)') for r in _load_done() if r.get('الموقع (Domain)')}
        st.session_state.scan_started = True
        st.rerun()

    # ── المحرك الآلي: chunk واحد لكل rerun — يريّح الاتصال ويحدّث الـ UI فعلياً ──
    if st.session_state.scan_started and st.session_state.domains_queue:
        queue = st.session_state.domains_queue
        done = st.session_state.done_domains
        processed_so_far = sum(1 for d in queue if d in done)

        st.progress(min(processed_so_far / total, 1.0))
        st.markdown(f"**تم فحص {processed_so_far} من {total}**")

        pending = [d for d in queue if d not in done]
        if pending:
            chunk = pending[:CHUNK_SIZE]
            with st.spinner(f"جاري فحص {processed_so_far + 1} إلى {min(processed_so_far + len(chunk), total)}..."):
                # with pool عادي جوه الـ chunk = لا threads معلقة بعد الختام (لا leak)
                with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = {executor.submit(scrape_single_domain, d, st.session_state.fast_mode): d for d in chunk}
                    for future in concurrent.futures.as_completed(futures):
                        d = futures[future]
                        try:
                            res = future.result()
                        except Exception:
                            res = error_row(d)
                        _save_row(res)  # يتخزن فوراً — لو الات عيط مفيش حاجة بتضيع
                        done.add(d)
            st.rerun()   # نفَس جديد للـ WebSocket — هون سر التغلب على idle timeout
        else:
            st.balloons()
            st.success(f"🎉 اكتمل فحص واكتشاف {processed_so_far} موقع بنجاح!")

# ---------------------------------------------------------------------------
# عرض النتائج المحفوظة (من الجلسة الحالية أو الجلسات السابقة — من القرص)
# ---------------------------------------------------------------------------
saved_rows = _load_done()
if saved_rows:
    st.markdown("### 📊 النتائج المخزنة")
    df_partial = pd.DataFrame(saved_rows)
    st.dataframe(df_partial, width='stretch')

    pbuf = io.BytesIO()
    with pd.ExcelWriter(pbuf, engine='openpyxl') as writer:
        df_partial.to_excel(writer, index=False, sheet_name='البيانات المستخرجة')
    pbuf.seek(0)
    st.download_button(
        label="📥 تحميل النتائج كملف Excel",
        data=pbuf,
        file_name="scraped_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.checkbox("🗑️ مسح النتائج المحفوظة وبدء من جديد"):
        if st.button("تأكيد المسح"):
            with _lock:
                if os.path.exists(RESULTS_FILE):
                    os.remove(RESULTS_FILE)
            st.session_state['partial_results'] = []
            st.success("تم مسح النتائج المحفوظة — يلا من الأول.")
