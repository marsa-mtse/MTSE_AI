# ==========================================================
# MTSE Marketing Engine — SaaS Edition v3.0  (FULL PLAN)
# ==========================================================
# الخطة الكاملة:
#  1. Cost Engine         — بنود + أسعار + سيناريوهات + تحذيرات
#  2. Social Media Engine — تحليل روابط + منصات
#  3. Multi-media Analysis— PDF/Word/Excel/صور/ZIP/رابط
#  4. Auto Content Type   — هندسي/مالي/تسويقي/قانوني/إداري
#  5. Final Report        — PDF احترافي شامل بكل الأقسام
# ==========================================================

import streamlit as st

st.set_page_config(
    page_title="MTSE Marketing Engine v3",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sqlite3, hashlib, datetime, io, os, re, json, zipfile
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch

try:
    import pdfplumber
    HAS_PDF = True
except Exception:
    HAS_PDF = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except Exception:
    HAS_DOCX = False

# requests / bs4 not in requirements — scraping disabled

# ==============================  STYLE  ==============================
st.markdown("""
<style>
body{background:linear-gradient(135deg,#0f172a,#111827);color:white;}
section[data-testid="stSidebar"]{background:#0b1120;}
.stButton>button{width:100%;border-radius:10px;height:42px;font-weight:600;
  border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05);
  color:white;transition:0.3s;}
.stButton>button:hover{background:linear-gradient(90deg,#00c6ff,#0072ff);
  transform:scale(1.03);border:none;}
.active-page{background:linear-gradient(90deg,#00c6ff,#0072ff);
  padding:10px 14px;border-radius:10px;font-weight:700;margin-bottom:8px;color:white;}
.stTextInput>div>div>input,.stTextArea textarea{text-align:right;}
h1,h2,h3{font-weight:700;letter-spacing:1px;}
</style>
""", unsafe_allow_html=True)

# ==============================  LANGUAGE  ==============================
if "lang" not in st.session_state:
    st.session_state.lang = "ar"

def t(ar, en):
    return ar if st.session_state.lang == "ar" else en

# ==============================  DATABASE  ==============================
conn = sqlite3.connect("mtse_v3.db", check_same_thread=False)
cur  = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY, password TEXT, role TEXT, plan TEXT,
    reports_used INTEGER DEFAULT 0, uploads_used INTEGER DEFAULT 0,
    created_at TEXT, expiry_date TEXT, billing_status TEXT, company TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT,
    file_name TEXT, created_at TEXT, summary TEXT, pdf_data BLOB)""")
cur.execute("""CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT, action TEXT, timestamp TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS crm_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, email TEXT, company TEXT, status TEXT, created_at TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT, owner TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS price_db (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT, unit TEXT, unit_price REAL, category TEXT, updated_at TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS past_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT, total_cost REAL, category TEXT, created_at TEXT)""")
conn.commit()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def log_activity(username, action):
    cur.execute("INSERT INTO activity_log (username,action,timestamp) VALUES (?,?,?)",
                (username, action, datetime.datetime.now().isoformat()))
    conn.commit()

def format_arabic(text):
    try:
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)

def reset_usage_if_new_month(username):
    cur.execute("SELECT created_at FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if row:
        try:
            cd  = datetime.datetime.fromisoformat(row[0])
            now = datetime.datetime.now()
            if cd.month != now.month or cd.year != now.year:
                cur.execute("UPDATE users SET reports_used=0,uploads_used=0,created_at=? WHERE username=?",
                            (now.isoformat(), username))
                conn.commit()
        except Exception:
            pass

# seed admin
cur.execute("SELECT * FROM users WHERE username='admin'")
if not cur.fetchone():
    cur.execute("INSERT INTO users (username,password,role,plan,created_at) VALUES (?,?,?,?,?)",
                ("admin", hash_password("admin@2026"), "admin", "Business",
                 datetime.datetime.now().isoformat()))
    conn.commit()

# seed price DB
cur.execute("SELECT COUNT(*) FROM price_db")
if cur.fetchone()[0] == 0:
    sample = [
        ("خرسانة مسلحة","م3",2500,"مدني"),("طوب أحمر","ألف طوبة",1800,"مدني"),
        ("حديد تسليح","طن",18000,"مدني"),("دهان داخلي","م2",45,"تشطيبات"),
        ("بلاط سيراميك","م2",120,"تشطيبات"),("أعمال حفر","م3",80,"ترابية"),
        ("عزل مائي","م2",95,"عزل"),("أبواب خشب","قطعة",1200,"نجارة"),
        ("نوافذ ألوميتال","م2",550,"ألوميتال"),("كابلات كهربائية","م.ط",35,"كهرباء"),
        ("سباكة صرف صحي","م.ط",120,"سباكة"),("تكييف مركزي","وحدة",8500,"ميكانيكا"),
    ]
    cur.executemany(
        "INSERT INTO price_db (item_name,unit,unit_price,category,updated_at) VALUES (?,?,?,?,?)",
        [(r[0],r[1],r[2],r[3],datetime.datetime.now().isoformat()) for r in sample])
    conn.commit()

PLAN_LIMITS  = {
    "Starter":{"reports":5,"uploads":5},
    "Pro":{"reports":25,"uploads":25},
    "Business":{"reports":9999,"uploads":9999}
}
PLAN_PRICING = {"Starter":29,"Pro":99,"Business":299}

for k,v in [("logged_in",False),("username",None),("role",None),("plan",None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ==============================  LOGIN  ==============================
if not st.session_state.logged_in:
    st.markdown("""<div style="text-align:center;padding:60px 0 20px">
        <h1>📊 MTSE Marketing Engine</h1>
        <p style="color:#94a3b8;">SaaS Platform v3.0 — Full Plan</p>
    </div>""", unsafe_allow_html=True)
    _, col, _ = st.columns([2,2,2])
    with col:
        lu = st.text_input(t("المستخدم","Username"))
        lp = st.text_input(t("كلمة المرور","Password"), type="password")
        if st.button(t("دخول","Login"), use_container_width=True):
            cur.execute("SELECT * FROM users WHERE username=?", (lu,))
            usr = cur.fetchone()
            if usr and usr[1] == hash_password(lp):
                st.session_state.logged_in = True
                st.session_state.username  = usr[0]
                st.session_state.role      = usr[2]
                st.session_state.plan      = usr[3]
                log_activity(usr[0], "Login")
                st.rerun()
            else:
                st.error(t("بيانات غير صحيحة","Invalid credentials"))
    st.stop()

reset_usage_if_new_month(st.session_state.username)
cur.execute("SELECT reports_used,uploads_used FROM users WHERE username=?",
            (st.session_state.username,))
_u = cur.fetchone()
reports_used = _u[0]; uploads_used = _u[1]
limits = PLAN_LIMITS[st.session_state.plan]

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# ==============================  SIDEBAR  ==============================
with st.sidebar:
    st.markdown("## 📊 MTSE v3")
    st.markdown(f"**{t('مرحباً','Hello')}** {st.session_state.username}")
    st.markdown(f"🎯 `{st.session_state.plan}`")
    st.markdown("---")
    if st.session_state.lang == "ar":
        if st.button("🌍 English"): st.session_state.lang="en"; st.rerun()
    else:
        if st.button("🌍 عربي"):    st.session_state.lang="ar"; st.rerun()
    st.markdown("---")

    def nav(pg, ar, en, icon):
        lbl = f"{icon}  {t(ar,en)}"
        if st.session_state.page == pg:
            st.markdown(f'<div class="active-page">{lbl}</div>', unsafe_allow_html=True)
        else:
            if st.button(lbl, use_container_width=True, key=f"nav_{pg}"):
                st.session_state.page = pg; st.rerun()

    nav("Dashboard",     "لوحة التحكم",    "Dashboard",      "🏠")
    nav("Analytics",     "تحليل البيانات", "Analytics",      "📊")
    nav("CostEngine",    "محرك المقايسات", "Cost Engine",    "🧮")
    nav("SocialMedia",   "تحليل السوشيال", "Social Media",   "📱")
    nav("MediaAnalysis", "تحليل الوسائط",  "Media Analysis", "📂")
    nav("AIEngine",      "محرك الذكاء",    "AI Engine",      "🤖")
    nav("Reports",       "التقارير",       "Reports",        "📁")
    nav("CRM",           "إدارة العملاء",  "CRM",            "👥")
    nav("Billing",       "الفواتير",       "Billing",        "💳")
    nav("Settings",      "الإعدادات",      "Settings",       "⚙")
    if st.session_state.role == "admin":
        nav("Admin","الإدارة","Admin","🔐")
    st.markdown("---")
    if st.button(t("خروج","Logout"), use_container_width=True):
        for k in ["logged_in","username","role","plan","page"]:
            st.session_state[k] = False if k=="logged_in" else None
        st.rerun()

page = st.session_state.page

# ==============================  AI LAYER  ==============================
def call_ai(system_p, user_p, max_tokens=1500):
    try:
        from groq import Groq
        key = st.secrets.get("GROQ_API_KEY", None)
        if key:
            cl = Groq(api_key=key)
            r  = cl.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"system","content":system_p},{"role":"user","content":user_p}],
                temperature=0.7, max_tokens=max_tokens)
            return r.choices[0].message.content
    except Exception:
        pass
    try:
        import openai
        key = st.secrets.get("OPENAI_API_KEY", None)
        if key:
            openai.api_key = key
            r = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":system_p},{"role":"user","content":user_p}],
                temperature=0.7)
            return r["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None

def generate_ai_strategy(df=None, dataset_type="Generic", question=None, content_type=None):
    summary = ""
    if df is not None:
        for col in df.select_dtypes(include=np.number).columns:
            summary += f"{col}: avg={round(df[col].mean(),2)}, max={round(df[col].max(),2)}\n"
    if question:
        sys_p = "You are a professional marketing consultant."
        usr_p = f"Question: {question}\n\nData:\n{summary}"
    else:
        sys_p = "You are a senior global marketing strategist."
        usr_p = f"Dataset: {dataset_type}\nContent: {content_type or 'General'}\nData:\n{summary}\n\nGenerate: 1.Executive Summary 2.Funnel Diagnosis 3.Budget Strategy 4.30-Day Plan 5.Scaling 6.Risk Assessment"
    result = call_ai(sys_p, usr_p)
    if result:
        return result
    lines = []
    if df is not None:
        if all(col in df.columns for col in ["revenue","spend"]):
            roas = (df["revenue"]/df["spend"]).mean()
            if roas < 1:   lines.append("⚠️ ROAS أقل من 1 — أعد توزيع الميزانية.")
            elif roas < 2: lines.append("📊 ROAS متوسط — ركّز على الحملات الرابحة.")
            else:          lines.append("✅ ROAS قوي — زد الميزانية بشكل استراتيجي.")
        if all(col in df.columns for col in ["impressions","clicks"]):
            ctr = (df["clicks"]/df["impressions"]).mean()*100
            lines.append(f"📈 متوسط CTR: {round(ctr,2)}% — {'يحتاج تحسين' if ctr<2 else 'جيد'}")
        lines += ["","**خطة 30/60/90 يوم:**","🔹 30 يوم → تحسين المقاييس الضعيفة",
                  "🔹 60 يوم → توسيع المقاييس القوية","🔹 90 يوم → أتمتة وتوسع"]
    else:
        lines.append("لم يتم رفع بيانات. ارفع ملف للحصول على تحليل أعمق.")
    return "\n".join(lines)

# ==============================  CONTENT TYPE  ==============================
CONTENT_KEYWORDS = {
    "هندسي":   ["خرسانة","حديد","عزل","بناء","كميات","بند","م3","م2","طن","concrete","rebar","construction","مقاولات"],
    "مالي":    ["revenue","profit","loss","spend","budget","cost","إيراد","ربح","خسارة","ميزانية","تكلفة","مصروف"],
    "تسويقي": ["impressions","clicks","ctr","roas","engagement","likes","followers","reach","campaign","إعلان","حملة"],
    "قانوني":  ["عقد","اتفاقية","شرط","contract","agreement","clause","legal","liability"],
    "إداري":   ["موظف","قسم","مهمة","جدول","employee","department","task","schedule","hr"],
    "seo":     ["keyword","search_volume","ranking","backlinks","domain","كلمة مفتاحية","سيو"],
}

def detect_content_type(text="", df=None):
    combined = text.lower()
    if df is not None:
        combined += " " + " ".join(df.columns.tolist()).lower()
    scores = {ct: sum(1 for kw in kws if kw in combined) for ct, kws in CONTENT_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "عام"

# ==============================  MEDIA EXTRACTOR  ==============================
def extract_text_from_file(uploaded):
    name = uploaded.name.lower()
    raw  = uploaded.read()
    uploaded.seek(0)
    if name.endswith(".pdf"):
        if HAS_PDF:
            try:
                with pdfplumber.open(io.BytesIO(raw)) as pdf:
                    text = "\n".join((pg.extract_text() or "") for pg in pdf.pages)
                return text, "PDF"
            except Exception as e:
                return f"(خطأ في قراءة PDF: {e})", "PDF"
        return "(مكتبة pdfplumber غير مثبتة)", "PDF"
    if name.endswith(".docx"):
        if HAS_DOCX:
            doc  = DocxDocument(io.BytesIO(raw))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return text, "Word"
        return "(تثبيت python-docx مطلوب)", "Word"
    if name.endswith((".xlsx",".xls")):
        return pd.read_excel(io.BytesIO(raw)).to_string(index=False), "Excel"
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(raw)).to_string(index=False), "CSV"
    if name.endswith((".png",".jpg",".jpeg",".webp")):
        return f"[صورة: {uploaded.name}]", "Image"
    if name.endswith(".zip"):
        texts = []
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            for zname in zf.namelist()[:20]:
                try:
                    content = zf.read(zname).decode("utf-8", errors="ignore")
                    texts.append(f"=== {zname} ===\n{content[:500]}")
                except Exception:
                    pass
        return "\n\n".join(texts), "ZIP"
    try:
        return raw.decode("utf-8", errors="ignore"), "Text"
    except Exception:
        return "(تعذّر قراءة الملف)", "Unknown"

def scrape_url(url):
    # requests + bs4 not in requirements.txt — return placeholder
    return f"(تحليل الروابط يتطلب إضافة requests و beautifulsoup4 إلى requirements.txt)"

# ==============================  COST HELPERS  ==============================
def parse_items_with_ai(text):
    sys_p = '''أنت مهندس مقايسات. استخرج بنود المشروع وأرجع JSON فقط:
[{"item":"اسم البند","unit":"الوحدة","qty":0}]
لا تضف أي نص خارج JSON.'''
    result = call_ai(sys_p, f"النص:\n{text[:3000]}")
    if result:
        try:
            clean = re.sub(r"```json|```","", result).strip()
            return json.loads(clean)
        except Exception:
            pass
    return []

def get_price_from_db(item_name):
    if not item_name:
        return None
    cur.execute("SELECT unit_price FROM price_db WHERE item_name LIKE ?", (f"%{item_name}%",))
    row = cur.fetchone()
    return row[0] if row else None

def cost_analysis_ai(items_df, scenarios):
    sys_p = "أنت خبير مقايسات ومستشار مشاريع."
    usr_p = f"""بنود المشروع:\n{items_df.to_string(index=False)}
السيناريوهات: محافظ={scenarios['conservative']:,.0f}  متوسط={scenarios['moderate']:,.0f}  مرتفع={scenarios['aggressive']:,.0f}
اكتب: 1.ملاحظات على البنود  2.بنود قد تكون ناقصة  3.تحذيرات تضخم  4.توصية نهائية"""
    return call_ai(sys_p, usr_p) or "أضف مفتاح Groq/OpenAI للتحليل الكامل."

# ==============================  PDF BUILDER  ==============================
def build_full_pdf(sections, username, report_lang="Arabic + English"):
    try:
        pdfmetrics.registerFont(TTFont('Amiri','Amiri-Regular.ttf'))
        ar_font = 'Amiri'
    except Exception:
        ar_font = 'Helvetica'

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=0.8*inch, bottomMargin=0.8*inch)
    els = []
    sty = getSampleStyleSheet()
    ar_s = ParagraphStyle('AR', parent=sty['Normal'], fontName=ar_font, fontSize=11, leading=20, alignment=2)
    en_s = sty['Normal']; h1 = sty['Heading1']; h2 = sty['Heading2']

    def watermark(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica",50); canvas.setFillGray(0.94)
        canvas.translate(A4[0]/2, A4[1]/2); canvas.rotate(40)
        canvas.drawCentredString(0,0,"MTSE Marketing Engine")
        canvas.restoreState()
        canvas.setFont("Helvetica",8)
        canvas.drawString(30,20,"MTSE Marketing Engine — Confidential")
        canvas.drawRightString(A4[0]-30,20,str(datetime.date.today()))

    def add_text(ar, en="", heading=False, sp=8):
        if report_lang in ["Arabic Only","Arabic + English"] and ar:
            p = h2 if heading else ar_s
            try:    els.append(Paragraph(format_arabic(ar), p))
            except: els.append(Paragraph(ar, p))
            els.append(Spacer(1,sp))
        if report_lang in ["English Only","Arabic + English"] and en:
            els.append(Paragraph(en, h2 if heading else en_s))
            els.append(Spacer(1,sp))

    els.append(Paragraph("📊 MTSE Marketing Engine", h1)); els.append(Spacer(1,10))
    add_text("تقرير التسويق الاحترافي الشامل","Enterprise Comprehensive Report", heading=True)
    els.append(Paragraph(f"Client: {username}", en_s))
    els.append(Paragraph(f"Date: {datetime.date.today()}", en_s))
    els.append(Paragraph(f"Content Type: {sections.get('content_type','General')}", en_s))
    els.append(PageBreak())

    add_text("الملخص التنفيذي","Executive Summary", heading=True)
    if sections.get("strategy"):
        for line in sections["strategy"].split("\n")[:10]:
            if line.strip(): add_text(line, line)
    els.append(Spacer(1,15))

    if sections.get("cost_table") is not None:
        df_cost = sections["cost_table"]
        add_text("جدول المقايسات","Cost Breakdown", heading=True)
        tdata = [list(df_cost.columns)]
        for _, row in df_cost.iterrows():
            tdata.append([str(v) for v in row])
        tbl = Table(tdata, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#0072ff")),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor("#f1f5f9")]),
        ]))
        els.append(tbl); els.append(Spacer(1,20))

    for key, ar_title, en_title in [
        ("social_analysis","تحليل السوشيال ميديا","Social Media Analysis"),
        ("media_analysis", "تحليل الوسائط","Media Analysis"),
        ("risks",          "تقييم المخاطر","Risk Assessment"),
        ("action_plan",    "خطة التنفيذ","Action Plan"),
    ]:
        if sections.get(key):
            add_text(ar_title, en_title, heading=True)
            for line in sections[key].split("\n")[:15]:
                if line.strip(): add_text(line, line)
            els.append(Spacer(1,15))

    doc.build(els, onFirstPage=watermark, onLaterPages=watermark)
    buf.seek(0)
    return buf

# ==========================================================
# ██  DASHBOARD
# ==========================================================
if page == "Dashboard":
    st.title(t("لوحة التحكم","Dashboard"))
    st.success(t(f"مرحباً {st.session_state.username} 👋", f"Welcome {st.session_state.username} 👋"))
    c1,c2,c3,c4 = st.columns(4)
    c1.metric(t("التقارير","Reports"), f"{reports_used}/{limits['reports']}")
    c2.metric(t("الرفعات","Uploads"),  f"{uploads_used}/{limits['uploads']}")
    c3.metric(t("الدور","Role"),  st.session_state.role)
    c4.metric(t("الخطة","Plan"),  st.session_state.plan)
    st.markdown("---")
    usage_df = pd.DataFrame({
        "Metric":[t("تقارير","Reports"),t("رفعات","Uploads")],
        "Used":[reports_used,uploads_used],
        "Limit":[limits['reports'],limits['uploads']]
    })
    fig = px.bar(usage_df, x="Metric", y=["Used","Limit"], barmode="group",
                 color_discrete_sequence=["#00c6ff","#0072ff"],
                 title=t("إحصائيات الاستخدام","Usage Statistics"))
    st.plotly_chart(fig, use_container_width=True)
    st.subheader(t("آخر النشاطات","Recent Activity"))
    logs = cur.execute(
        "SELECT action,timestamp FROM activity_log WHERE username=? ORDER BY id DESC LIMIT 8",
        (st.session_state.username,)).fetchall()
    for lg in logs:
        st.write(f"🔹 {lg[0]}  —  {lg[1][:19]}")
    if not logs: st.info(t("لا يوجد نشاط","No activity yet"))

# ==========================================================
# ██  ANALYTICS
# ==========================================================
elif page == "Analytics":
    st.title(t("تحليل البيانات","Data Analytics"))
    if uploads_used >= limits["uploads"]:
        st.error(t("تجاوزت حد الرفع","Upload limit reached")); st.stop()
    uf = st.file_uploader(t("ارفع CSV أو Excel","Upload CSV/Excel"), type=["csv","xlsx"])
    if uf:
        cur.execute("UPDATE users SET uploads_used=uploads_used+1 WHERE username=?", (st.session_state.username,))
        conn.commit(); log_activity(st.session_state.username, f"Uploaded: {uf.name}")
        df = pd.read_csv(uf) if uf.name.endswith(".csv") else pd.read_excel(uf)
        st.session_state["df"] = df; st.session_state["uploaded_name"] = uf.name
        ct = detect_content_type(df=df); st.session_state["content_type"] = ct
        cols_lower = [x.lower() for x in df.columns]
        dtype = "Generic"
        if "impressions" in cols_lower and "clicks" in cols_lower: dtype="Paid Ads"
        elif "likes" in cols_lower:   dtype="Social Organic"
        elif "keyword" in cols_lower: dtype="SEO"
        elif "revenue" in cols_lower: dtype="ROI/ROAS"
        st.session_state["dataset_type"] = dtype
        st.success(f"✅ {uf.name}")
        st.info(f"📂 {t('النوع','Detected')}: **{dtype}**  |  {t('المحتوى','Content')}: **{ct}**")
        st.dataframe(df.head(), use_container_width=True)
        num_cols = df.select_dtypes(include=np.number).columns
        if len(num_cols):
            st.markdown("---"); st.header(t("مقاييس الأداء","Performance Metrics"))
            mcols = st.columns(min(4,len(num_cols)))
            for i,col in enumerate(num_cols):
                mcols[i%4].metric(col, round(df[col].mean(),2))
            fig = px.line(df[num_cols], title=t("أداء المقاييس","Metrics Trend"),
                          color_discrete_sequence=px.colors.qualitative.Bold)
            st.plotly_chart(fig, use_container_width=True)
            st.subheader(t("توقع الاتجاه","Trend Prediction"))
            col_ch = st.selectbox(t("اختر عمود","Select column"), num_cols)
            X = np.arange(len(df)).reshape(-1,1)
            y = df[col_ch].values.reshape(-1,1)
            nxt = LinearRegression().fit(X,y).predict([[len(df)]])[0][0]
            st.success(f"📈 {t('القيمة التالية','Next Value')}: **{round(float(nxt),2)}**")
            st.markdown("---"); st.subheader(t("رؤى سريعة","Quick Insights"))
            for col in num_cols:
                icon = "⚠️" if df[col].mean() < df[col].max()*0.5 else "✅"
                st.write(f"{icon} **{col}**: avg={round(df[col].mean(),2)}")

# ==========================================================
# ██  COST ENGINE
# ==========================================================
elif page == "CostEngine":
    st.title(t("محرك المقايسات الكامل","Full Cost Engine"))
    tab1,tab2,tab3,tab4 = st.tabs([
        t("إدخال يدوي","Manual Entry"),
        t("استخراج من ملف/نص","Extract from File/Text"),
        t("قاعدة الأسعار","Price Database"),
        t("مقارنة المشاريع","Project Comparison")
    ])

    with tab1:
        st.subheader(t("إدخال بنود يدوياً","Manual Item Entry"))
        if "cost_items" not in st.session_state:
            st.session_state.cost_items = []
        col_a,col_b,col_c,col_d = st.columns([3,2,2,2])
        ci_name  = col_a.text_input(t("اسم البند","Item Name"), key="ci_name")
        ci_unit  = col_b.text_input(t("الوحدة","Unit"),         key="ci_unit")
        ci_qty   = col_c.number_input(t("الكمية","Qty"), min_value=0.0, key="ci_qty")
        auto_p   = get_price_from_db(ci_name)
        ci_price = col_d.number_input(t("سعر الوحدة","Unit Price"),
                                      value=float(auto_p) if auto_p else 0.0, key="ci_price")
        if auto_p: col_d.caption(t("✔ من قاعدة البيانات","✔ From DB"))
        ca,cb = st.columns(2)
        if ca.button(t("➕ أضف البند","➕ Add Item"), use_container_width=True):
            if ci_name and ci_qty > 0:
                st.session_state.cost_items.append({
                    "البند":ci_name,"الوحدة":ci_unit,"الكمية":ci_qty,
                    "سعر الوحدة":ci_price,"الإجمالي":round(ci_qty*ci_price,2)
                })
                st.success(t("تمت الإضافة","Added"))
        if cb.button(t("🗑 مسح الكل","🗑 Clear All"), use_container_width=True):
            st.session_state.cost_items = []

        if st.session_state.cost_items:
            items_df = pd.DataFrame(st.session_state.cost_items)
            st.dataframe(items_df, use_container_width=True)
            direct_cost = items_df["الإجمالي"].sum()
            st.metric(t("التكلفة المباشرة الإجمالية","Total Direct Cost"), f"{direct_cost:,.0f}")
            st.markdown("---"); st.subheader(t("معاملات الحساب","Parameters"))
            c1,c2,c3 = st.columns(3)
            ind_p = c1.slider(t("مصاريف غير مباشرة %","Indirect %"),0,30,10)
            wst_p = c1.slider(t("هالك %","Waste %"),0,20,5)
            adm_p = c2.slider(t("إدارة %","Admin %"),0,20,7)
            prf_p = c2.slider(t("ربح %","Profit %"),0,50,20)
            inf_p = c3.slider(t("مخاطر تضخم %","Inflation %"),0,20,5)
            base = direct_cost * (1 + (ind_p+wst_p+adm_p+inf_p)/100)
            scenarios = {
                t("محافظ","Conservative"): base*(1+prf_p*0.7/100),
                t("متوسط","Moderate"):     base*(1+prf_p/100),
                t("مرتفع","Aggressive"):   base*(1+prf_p*1.3/100),
            }
            vals = list(scenarios.values())
            sc1,sc2,sc3 = st.columns(3)
            sc1.metric(list(scenarios.keys())[0], f"{vals[0]:,.0f}")
            sc2.metric(list(scenarios.keys())[1], f"{vals[1]:,.0f}")
            sc3.metric(list(scenarios.keys())[2], f"{vals[2]:,.0f}")
            fig = px.bar(x=list(scenarios.keys()), y=vals, color=list(scenarios.keys()),
                         color_discrete_sequence=["#00c6ff","#0072ff","#7c3aed"],
                         title=t("السيناريوهات","Scenarios"),
                         labels={"x":t("السيناريو","Scenario"),"y":t("التكلفة","Cost")})
            st.plotly_chart(fig, use_container_width=True)
            all_db = [r[0] for r in cur.execute("SELECT item_name FROM price_db").fetchall()]
            entered = [it["البند"] for it in st.session_state.cost_items]
            missing = [x for x in all_db if x not in entered][:5]
            if missing:
                st.warning(t(f"⚠️ بنود قد تكون ناقصة: {', '.join(missing)}",
                              f"⚠️ Possibly missing: {', '.join(missing)}"))
            if st.button(t("🤖 تحليل ذكي","🤖 AI Analysis"), use_container_width=True):
                with st.spinner(t("جاري...","Analyzing...")):
                    ai_c = cost_analysis_ai(items_df,{"conservative":vals[0],"moderate":vals[1],"aggressive":vals[2]})
                st.markdown("### " + t("التحليل الذكي","AI Analysis")); st.markdown(ai_c)
            st.session_state["cost_table"] = items_df; st.session_state["cost_scenarios"] = scenarios
            st.markdown("---")
            proj_name = st.text_input(t("اسم المشروع للحفظ","Project Name"), key="save_proj")
            if st.button(t("💾 حفظ في المشاريع السابقة","💾 Save"), use_container_width=True):
                if proj_name:
                    cur.execute("INSERT INTO past_projects (project_name,total_cost,category,created_at) VALUES (?,?,?,?)",
                                (proj_name, vals[1], "مدني", datetime.datetime.now().isoformat()))
                    conn.commit(); st.success(t("تم الحفظ","Saved"))

    with tab2:
        st.subheader(t("استخراج بنود تلقائياً","AI Auto-Extract Items"))
        src = st.radio(t("المصدر","Source"), [t("نص","Text"), t("ملف","File")], horizontal=True)
        raw_text = ""
        if src == t("نص","Text"):
            raw_text = st.text_area(t("الصق نص المشروع","Paste project text"), height=200)
        else:
            ext_f = st.file_uploader(t("ارفع الملف","Upload"), key="ce_file")
            if ext_f:
                raw_text, ftype = extract_text_from_file(ext_f)
                st.info(f"📂 {ftype}")
                with st.expander(t("عرض","Preview")):
                    st.text(raw_text[:1500])
        if st.button(t("🤖 استخرج البنود","🤖 Extract"), use_container_width=True):
            if raw_text.strip():
                with st.spinner(t("جاري الاستخراج...","Extracting...")):
                    extracted = parse_items_with_ai(raw_text)
                if extracted:
                    st.success(t(f"تم استخراج {len(extracted)} بند",f"Extracted {len(extracted)} items"))
                    for it in extracted:
                        price = get_price_from_db(it.get("item","")) or 0
                        st.session_state.cost_items.append({
                            "البند":it.get("item",""),"الوحدة":it.get("unit",""),
                            "الكمية":float(it.get("qty",0)),
                            "سعر الوحدة":price,"الإجمالي":round(float(it.get("qty",0))*price,2)
                        })
                    st.dataframe(pd.DataFrame(st.session_state.cost_items), use_container_width=True)
                else:
                    st.warning(t("لم يُستخرج شيء — أضف مفتاح AI","Nothing extracted — add AI key"))
            else:
                st.warning(t("أدخل نصاً","Enter text"))

    with tab3:
        st.subheader(t("قاعدة بيانات الأسعار","Price Database"))
        all_p = cur.execute("SELECT id,item_name,unit,unit_price,category FROM price_db").fetchall()
        st.dataframe(pd.DataFrame(all_p,columns=["ID","البند","الوحدة","السعر","الفئة"]), use_container_width=True)
        st.markdown("---")
        p1,p2,p3,p4 = st.columns(4)
        pn=p1.text_input(t("البند","Item"),key="pdb_n"); pu=p2.text_input(t("الوحدة","Unit"),key="pdb_u")
        pp=p3.number_input(t("السعر","Price"),min_value=0.0,key="pdb_p"); pc=p4.text_input(t("الفئة","Cat"),key="pdb_c")
        if st.button(t("حفظ","Save"), use_container_width=True):
            cur.execute("SELECT id FROM price_db WHERE item_name=?",(pn,))
            ex = cur.fetchone()
            if ex:
                cur.execute("UPDATE price_db SET unit_price=?,updated_at=? WHERE item_name=?",
                            (pp,datetime.datetime.now().isoformat(),pn))
            else:
                cur.execute("INSERT INTO price_db (item_name,unit,unit_price,category,updated_at) VALUES (?,?,?,?,?)",
                            (pn,pu,pp,pc,datetime.datetime.now().isoformat()))
            conn.commit(); st.success(t("تم","Saved")); st.rerun()

    with tab4:
        st.subheader(t("مقارنة بمشاريع سابقة","Compare with Past Projects"))
        past = cur.execute("SELECT project_name,total_cost,category,created_at FROM past_projects").fetchall()
        if past:
            df_past = pd.DataFrame(past,columns=["المشروع","التكلفة","الفئة","التاريخ"])
            st.dataframe(df_past, use_container_width=True)
            fig_p = px.bar(df_past,x="المشروع",y="التكلفة",color="الفئة",title=t("مقارنة","Comparison"))
            st.plotly_chart(fig_p, use_container_width=True)
            avg_c = df_past["التكلفة"].mean()
            cur_vals = list(st.session_state.get("cost_scenarios",{}).values())
            if len(cur_vals) > 1:
                diff = (cur_vals[1]-avg_c)/avg_c*100
                if   diff >  20: st.error(f"⚠️ {t('أعلى من المتوسط بنسبة','Above avg by')} {round(diff,1)}%")
                elif diff < -20: st.warning(f"💡 {t('أقل من المتوسط','Below average — verify')}")
                else:            st.success(f"✅ {t('في النطاق الطبيعي','Within normal range')}")
        else:
            st.info(t("لا توجد مشاريع سابقة","No past projects"))

# ==========================================================
# ██  SOCIAL MEDIA ENGINE
# ==========================================================
elif page == "SocialMedia":
    st.title(t("محرك تحليل السوشيال ميديا","Social Media Engine"))
    tab_s1,tab_s2 = st.tabs([t("تحليل الرابط","URL Analysis"),t("تحليل بيانات","Data Analysis")])

    with tab_s1:
        st.subheader(t("أدخل رابط الصفحة أو الحساب","Enter Page/Account URL"))
        social_url = st.text_input(t("الرابط","URL"),
            placeholder="https://www.facebook.com/page  or  https://www.tiktok.com/@user")
        platform = "عام"
        if social_url:
            for plat,kw in [("Facebook","facebook.com"),("Instagram","instagram.com"),
                             ("TikTok","tiktok.com"),("YouTube","youtube.com"),
                             ("X/Twitter","twitter.com"),("LinkedIn","linkedin.com")]:
                if kw in social_url: platform=plat; break
            st.info(f"🌐 {t('المنصة','Platform')}: **{platform}**")
        if st.button(t("🔍 تحليل","🔍 Analyze"), use_container_width=True):
            if not social_url.strip():
                st.warning(t("أدخل رابطاً","Enter URL"))
            else:
                with st.spinner(t("جاري الاستخراج...","Scraping...")):
                    scraped = scrape_url(social_url)
                ctx = scraped[:3000] if len(scraped)>50 else f"URL: {social_url}\nPlatform: {platform}"
                sys_p = f"""أنت خبير تسويق رقمي متخصص في {platform}.
قدّم تحليلاً شاملاً يشمل:
1. تحليل الأداء الحالي  2. هوية العلامة التجارية والجمهور
3. نقاط القوة والضعف والفجوات  4. خطة محتوى (7 أفكار)
5. جدول نشر أسبوعي  6. توصيات تحسين CTA  7. استراتيجية نمو 30 يوم"""
                with st.spinner(t("جاري التحليل...","Analyzing...")):
                    result = call_ai(sys_p, f"بيانات الصفحة:\n{ctx}")
                if not result:
                    result = f"""**تحليل {platform} — توصيات عامة:**
- نشر محتوى 3-5 مرات أسبوعياً بانتظام
- الفيديو القصير يحقق أعلى وصول على {platform}
- تحسين الـ Bio مع CTA واضح + رابط مباشر
- التفاعل مع التعليقات خلال أول ساعة
- استخدام 5-10 هاشتاقات متخصصة لكل منشور
أضف مفتاح Groq/OpenAI لتحليل مخصص للصفحة."""
                st.markdown("### 📊 " + t("نتيجة التحليل","Analysis")); st.markdown(result)
                st.session_state["social_analysis"] = result
                log_activity(st.session_state.username, f"Social: {platform}")

    with tab_s2:
        st.subheader(t("تحليل بيانات السوشيال","Social Data Analysis"))
        df = st.session_state.get("df",None)
        if df is None:
            st.info(t("ارفع ملف من صفحة التحليلات أولاً","Upload in Analytics first"))
        else:
            df.columns = [x.lower() for x in df.columns]
            cols_l = list(df.columns)
            if "impressions" in cols_l and "clicks" in cols_l:
                df["CTR"] = (df["clicks"]/df["impressions"]*100).round(2)
                if "spend" in cols_l and "revenue" in cols_l:
                    df["ROAS"] = (df["revenue"]/df["spend"]).round(2)
                cc1,cc2,cc3 = st.columns(3)
                cc1.metric("Avg CTR", f"{df['CTR'].mean():.2f}%")
                cc2.metric("Avg Impressions", f"{df['impressions'].mean():,.0f}")
                if "ROAS" in df.columns: cc3.metric("Avg ROAS", f"{df['ROAS'].mean():.2f}x")
                fig = px.scatter(df,x="impressions",y="clicks",color="CTR",title="CTR vs Impressions",
                                 color_continuous_scale="blues")
                st.plotly_chart(fig, use_container_width=True)
            elif "likes" in cols_l:
                eng = [x for x in ["likes","comments","shares","saves"] if x in cols_l]
                if eng:
                    df["Engagement"] = df[eng].sum(axis=1)
                    fig = px.bar(df.head(20),y="Engagement",title=t("التفاعل","Engagement"),
                                 color="Engagement",color_continuous_scale="blues")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(t("ارفع ملف سوشيال ميديا (impressions/clicks أو likes/comments)",
                           "Upload social media file with impressions/clicks or likes/comments"))

# ==========================================================
# ██  MEDIA ANALYSIS
# ==========================================================
elif page == "MediaAnalysis":
    st.title(t("تحليل الوسائط المتعددة","Multi-Media Analysis"))
    st.info(t("يدعم: PDF • Word • Excel • CSV • صور • ZIP • نص • رابط",
               "Supports: PDF • Word • Excel • CSV • Images • ZIP • Text • URL"))
    src_type = st.radio(t("نوع المدخل","Input Type"),
                        [t("ملف","File"),t("رابط URL","URL"),t("نص مباشر","Direct Text")],horizontal=True)
    extracted_text = ""; file_type_lbl = ""
    if src_type == t("ملف","File"):
        mf = st.file_uploader(t("ارفع الملف","Upload"),
             type=["pdf","docx","xlsx","xls","csv","png","jpg","jpeg","webp","zip","txt"])
        if mf:
            with st.spinner(t("جاري الاستخراج...","Extracting...")):
                extracted_text, file_type_lbl = extract_text_from_file(mf)
            st.info(f"📂 {file_type_lbl} | {len(extracted_text)} {t('حرف','chars')}")
            with st.expander(t("عرض","Preview")): st.text(extracted_text[:2000])
    elif src_type == t("رابط URL","URL"):
        mu = st.text_input(t("الرابط","URL"), placeholder="https://...")
        if st.button(t("استخراج","Fetch"), use_container_width=True) and mu:
            with st.spinner(t("جاري...","Fetching...")):
                extracted_text = scrape_url(mu); file_type_lbl = "URL"
            st.info(f"🌐 {len(extracted_text)} {t('حرف','chars')}")
            with st.expander(t("عرض","Preview")): st.text(extracted_text[:2000])
    else:
        extracted_text = st.text_area(t("الصق النص","Paste Text"), height=200)
        file_type_lbl  = "Text"

    if extracted_text and extracted_text.strip():
        ct = detect_content_type(text=extracted_text)
        st.session_state["content_type"] = ct
        st.success(f"🔍 {t('نوع المحتوى','Content Type')}: **{ct}**")
        analysis_type = st.selectbox(t("نوع التحليل","Analysis Type"),
            [t("تحليل شامل","Full Analysis"),t("ملخص تنفيذي","Executive Summary"),
             t("استخراج البنود والكميات","Extract Items & Quantities"),
             t("تحليل مالي","Financial Analysis"),t("تحليل مخاطر","Risk Analysis"),
             t("توصيات استراتيجية","Strategic Recommendations")])
        if st.button(t("🤖 حلل الآن","🤖 Analyze Now"), use_container_width=True):
            sys_p = f"أنت خبير تحليل وثائق متخصص في المحتوى {ct}. نوع التحليل: {analysis_type}. قدّم تحليلاً منظماً."
            with st.spinner(t("جاري التحليل...","Analyzing...")):
                result = call_ai(sys_p, f"نوع الملف: {file_type_lbl}\n\n{extracted_text[:4000]}", max_tokens=2000)
            if not result:
                result = f"**{t('تحليل تلقائي','Auto Analysis')} — {file_type_lbl}:**\n- النوع: {ct}\n- الحجم: {len(extracted_text)} حرف\nأضف مفتاح AI للتحليل الكامل."
            st.markdown("### 📊 " + t("نتيجة التحليل","Result")); st.markdown(result)
            st.session_state["media_analysis"] = result
            log_activity(st.session_state.username, f"Media: {file_type_lbl}/{ct}")

# ==========================================================
# ██  AI ENGINE
# ==========================================================
elif page == "AIEngine":
    st.title(t("محرك الذكاء الاصطناعي","AI Engine"))
    tab1,tab2,tab3 = st.tabs([t("الاستراتيجية","Marketing Strategy"),
                               t("المساعد الذكي","AI Assistant"),t("تحليل سريع","Quick Analysis")])
    with tab1:
        df=st.session_state.get("df",None); dtype=st.session_state.get("dataset_type","Generic"); ctype=st.session_state.get("content_type","عام")
        if df is None: st.info(t("ارفع ملف من صفحة التحليلات","Upload file in Analytics"))
        else: st.info(f"📂 {dtype} | {ctype}")
        if st.button(t("🚀 توليد استراتيجية كاملة","🚀 Generate Full Strategy"), use_container_width=True):
            with st.spinner(t("جاري التوليد...","Generating...")):
                strat = generate_ai_strategy(df=df,dataset_type=dtype,content_type=ctype)
            st.markdown("### 📊"); st.markdown(strat)
            st.session_state["strategy_output"] = strat
            with st.spinner(t("استخراج المخاطر وخطة التنفيذ...","Extracting risks & plan...")):
                st.session_state["risks"]       = call_ai("Extract risks only as bullet points.", strat) or ""
                st.session_state["action_plan"] = call_ai("Extract action plan/timeline only as bullet points.", strat) or ""
            log_activity(st.session_state.username,"Generated AI Strategy")
    with tab2:
        df=st.session_state.get("df",None)
        q=st.text_area(t("اسأل المساعد","Ask Assistant"),placeholder=t("أي سؤال...","Any question..."))
        if st.button(t("🤖 اسأل","🤖 Ask"), use_container_width=True):
            if q.strip():
                with st.spinner("..."): ans=generate_ai_strategy(df=df,question=q)
                st.markdown("### 💬"); st.markdown(ans)
            else: st.warning(t("اكتب سؤالاً","Write a question"))
    with tab3:
        qt=st.text_area(t("أي نص للتحليل السريع","Any text for quick analysis"), height=150)
        if st.button(t("حلل","Analyze"), use_container_width=True) and qt.strip():
            ct2=detect_content_type(text=qt)
            with st.spinner("..."): r=call_ai(f"أنت خبير {ct2}. قدّم تحليلاً في 5 نقاط.", qt) or t("أضف مفتاح AI","Add AI key")
            st.markdown(r)

# ==========================================================
# ██  REPORTS
# ==========================================================
elif page == "Reports":
    st.title(t("التقارير الاحترافية","Professional Reports"))
    if reports_used >= limits["reports"]:
        st.error(t("تجاوزت حد التقارير","Report limit reached")); st.stop()
    report_lang = st.selectbox(t("لغة التقرير","Language"),["Arabic + English","Arabic Only","English Only"])
    has_s = bool(st.session_state.get("strategy_output"))
    has_c = st.session_state.get("cost_table") is not None
    has_sm = bool(st.session_state.get("social_analysis"))
    has_m = bool(st.session_state.get("media_analysis"))
    st.markdown(f"""
| القسم | الحالة |
|---|---|
| {t("الاستراتيجية","Strategy")} | {"✅" if has_s else "⬜ — "+t("اذهب لـ AI Engine","Go to AI Engine")} |
| {t("المقايسات","Cost Table")} | {"✅" if has_c else "⬜ — "+t("اذهب لـ Cost Engine","Go to Cost Engine")} |
| {t("السوشيال","Social")} | {"✅" if has_sm else "⬜ — "+t("اذهب لـ Social Media","Go to Social Media")} |
| {t("الوسائط","Media")} | {"✅" if has_m else "⬜ — "+t("اذهب لـ Media Analysis","Go to Media Analysis")} |
""")
    if st.button(t("📄 إنشاء التقرير الشامل","📄 Generate Full Report"), use_container_width=True):
        sections = {
            "strategy":st.session_state.get("strategy_output",""),
            "cost_table":st.session_state.get("cost_table",None),
            "social_analysis":st.session_state.get("social_analysis",""),
            "media_analysis":st.session_state.get("media_analysis",""),
            "content_type":st.session_state.get("content_type","عام"),
            "risks":st.session_state.get("risks",""),
            "action_plan":st.session_state.get("action_plan",""),
        }
        fname = st.session_state.get("uploaded_name","report")
        with st.spinner(t("جاري بناء التقرير...","Building PDF...")):
            pdf_buf = build_full_pdf(sections, st.session_state.username, report_lang)
        cur.execute("INSERT INTO reports (username,file_name,created_at,summary,pdf_data) VALUES (?,?,?,?,?)",
                    (st.session_state.username,fname,datetime.datetime.now().isoformat(),
                     sections["strategy"][:200],pdf_buf.getvalue()))
        conn.commit()
        cur.execute("UPDATE users SET reports_used=reports_used+1 WHERE username=?",(st.session_state.username,))
        conn.commit()
        log_activity(st.session_state.username, f"Generated Full Report: {fname}")
        st.success(t("✅ تم إنشاء التقرير","✅ Report generated"))
        st.download_button(t("⬇ تحميل التقرير","⬇ Download"),data=pdf_buf,
                           file_name="MTSE_Full_Report.pdf",mime="application/pdf")
    st.markdown("---"); st.subheader(t("أرشيف التقارير","Archive"))
    arch = cur.execute("SELECT id,file_name,created_at,pdf_data FROM reports WHERE username=? ORDER BY id DESC",
                       (st.session_state.username,)).fetchall()
    for rep in arch:
        ra,rb = st.columns([4,1])
        ra.write(f"📄 {rep[1]} — {rep[2][:19]}")
        rb.download_button(t("تحميل","Download"),data=rep[3],
                           file_name=f"{rep[1]}.pdf",mime="application/pdf",key=f"dl_{rep[0]}")
    if not arch: st.info(t("لا توجد تقارير","No reports yet"))

# ==========================================================
# ██  CRM
# ==========================================================
elif page == "CRM":
    st.title(t("نظام إدارة العملاء","CRM System"))
    c1,c2,c3 = st.columns(3)
    ln=c1.text_input(t("الاسم","Name")); le=c2.text_input(t("البريد","Email")); lc=c3.text_input(t("الشركة","Company"))
    if st.button(t("➕ إضافة","➕ Add"), use_container_width=True):
        if ln:
            cur.execute("INSERT INTO crm_leads (name,email,company,status,created_at) VALUES (?,?,?,?,?)",
                        (ln,le,lc,"New",datetime.datetime.now().isoformat()))
            conn.commit(); st.success(t("تمت الإضافة","Added"))
    st.markdown("---")
    leads = cur.execute("SELECT id,name,email,company,status,created_at FROM crm_leads").fetchall()
    if leads:
        st.dataframe(pd.DataFrame(leads,columns=["ID","Name","Email","Company","Status","Date"]),use_container_width=True)
    else: st.info(t("لا يوجد عملاء","No leads"))

# ==========================================================
# ██  BILLING
# ==========================================================
elif page == "Billing":
    st.title(t("الفواتير","Billing"))
    cur.execute("SELECT billing_status,expiry_date FROM users WHERE username=?",(st.session_state.username,))
    bi=cur.fetchone()
    c1,c2=st.columns(2)
    c1.metric(t("حالة الاشتراك","Status"),bi[0] if bi and bi[0] else t("نشط","Active"))
    c2.metric(t("الانتهاء","Expiry"),bi[1][:10] if bi and bi[1] else t("غير محدد","Not Set"))
    st.markdown("---")
    up=st.selectbox(t("ترقية الخطة","Upgrade"),["Starter","Pro","Business"],
                    format_func=lambda x: f"{x} — ${PLAN_PRICING[x]}/mo")
    if st.button(t("ترقية (محاكاة)","Upgrade (Sim)"),use_container_width=True):
        exp=(datetime.datetime.now()+datetime.timedelta(days=30)).isoformat()
        cur.execute("UPDATE users SET plan=?,billing_status='Active',expiry_date=? WHERE username=?",
                    (up,exp,st.session_state.username))
        conn.commit(); st.session_state.plan=up
        st.success(t("تم","Done")); log_activity(st.session_state.username,f"Upgraded to {up}")
    st.markdown("---"); st.subheader(t("مولد الفواتير","Invoice Generator"))
    ic=st.text_input(t("اسم العميل","Client")); ia=st.number_input(t("المبلغ","Amount"),min_value=0.0)
    if st.button(t("📄 إنشاء فاتورة","📄 Invoice"),use_container_width=True):
        b2=io.BytesIO(); d2=SimpleDocTemplate(b2,pagesize=A4); s2=getSampleStyleSheet()
        e2=[Paragraph("MTSE Marketing Engine",s2["Heading1"]),Spacer(1,20),
            Paragraph(f"To: {ic}",s2["Normal"]),Paragraph(f"Date: {datetime.date.today()}",s2["Normal"]),Spacer(1,10)]
        tt=Table([["Description","Amount"],["Marketing Services",f"${ia:,.2f}"]])
        tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor("#0072ff")),
                                ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                                ('GRID',(0,0),(-1,-1),0.5,colors.grey)]))
        e2.append(tt); d2.build(e2); b2.seek(0)
        st.download_button(t("⬇ تحميل","⬇ Download"),data=b2,file_name="invoice.pdf",mime="application/pdf")

# ==========================================================
# ██  SETTINGS
# ==========================================================
elif page == "Settings":
    st.title(t("الإعدادات","Settings"))
    st.subheader(t("تغيير كلمة المرور","Change Password"))
    p1=st.text_input(t("الجديدة","New"),type="password",key="sp1")
    p2=st.text_input(t("تأكيد","Confirm"),type="password",key="sp2")
    if st.button(t("حفظ","Save"),use_container_width=True):
        if p1 and p1==p2:
            cur.execute("UPDATE users SET password=? WHERE username=?",(hash_password(p1),st.session_state.username))
            conn.commit(); st.success(t("تم","Updated"))
        else: st.error(t("غير متطابق","Mismatch"))
    st.markdown("---"); st.subheader("White Label")
    wn=st.text_input(t("العلامة التجارية","Brand")); wl=st.file_uploader(t("الشعار","Logo"),type=["png","jpg"]); wd=st.text_input(t("الدومين","Domain"))
    if wn: st.markdown(f"### {wn}")
    if wl: st.image(wl,width=150)
    if wd: st.info(f"🌐 {wd} ({t('محاكاة','Sim')})")
    st.markdown("---"); st.subheader(t("حملة بريد إلكتروني","Email Campaign"))
    es=st.text_input(t("الموضوع","Subject")); eb=st.text_area(t("المحتوى","Body"))
    if st.button(t("إرسال (محاكاة)","Send (Sim)"),use_container_width=True):
        st.success(t("تم الإرسال (محاكاة)","Sent (Sim)"))

# ==========================================================
# ██  ADMIN
# ==========================================================
elif page == "Admin" and st.session_state.role == "admin":
    st.title(t("لوحة الإدارة","Admin Panel"))
    tab_u,tab_p,tab_t,tab_l = st.tabs([t("المستخدمون","Users"),t("الخطط","Plans"),t("الفرق","Teams"),t("السجل","Logs")])
    with tab_u:
        all_u=cur.execute("SELECT username,role,plan,reports_used,uploads_used FROM users").fetchall()
        st.dataframe(pd.DataFrame(all_u,columns=["User","Role","Plan","Reports","Uploads"]),use_container_width=True)
        st.markdown("---"); st.subheader(t("إنشاء مستخدم","Create User"))
        cu1,cu2=st.columns(2)
        nu=cu1.text_input("Username",key="au"); np_=cu2.text_input("Password",type="password",key="ap")
        cu3,cu4=st.columns(2)
        npl=cu3.selectbox("Plan",["Starter","Pro","Business"],key="apl")
        nrl=cu4.selectbox("Role",["Analyst","Viewer","Marketing Manager"],key="arl")
        if st.button("Create",use_container_width=True):
            try:
                cur.execute("INSERT INTO users (username,password,role,plan,created_at) VALUES (?,?,?,?,?)",
                            (nu,hash_password(np_),nrl,npl,datetime.datetime.now().isoformat()))
                conn.commit(); st.success("Created")
            except: st.error("Already exists")
    with tab_p:
        tu=st.text_input(t("المستخدم","User"),key="tpu"); tp=st.selectbox(t("الخطة","Plan"),["Starter","Pro","Business"],key="tpp")
        if st.button(t("تحديث","Update"),use_container_width=True):
            cur.execute("UPDATE users SET plan=? WHERE username=?",(tp,tu)); conn.commit(); st.success("Updated")
    with tab_t:
        tn=st.text_input(t("الشركة","Company"),key="ttn")
        if st.button(t("إنشاء فريق","Create Team"),use_container_width=True):
            cur.execute("INSERT INTO teams (company,owner) VALUES (?,?)",(tn,st.session_state.username)); conn.commit(); st.success("Done")
        au2=st.text_input(t("مستخدم","User"),key="tau"); ac2=st.text_input(t("شركة","Company"),key="tac")
        if st.button(t("تعيين","Assign"),use_container_width=True):
            cur.execute("UPDATE users SET company=? WHERE username=?",(ac2,au2)); conn.commit(); st.success("Done")
    with tab_l:
        lg=cur.execute("SELECT username,action,timestamp FROM activity_log ORDER BY id DESC LIMIT 200").fetchall()
        if lg: st.dataframe(pd.DataFrame(lg,columns=["User","Action","Time"]),use_container_width=True)
        else:  st.info("No logs")
