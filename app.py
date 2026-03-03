# ==========================================================
# MTSE AI — FULL ENTERPRISE MASTER BUILD (FINAL STABLE)
# ==========================================================

import streamlit as st
from groq import Groq
import pandas as pd
import numpy as np
import sqlite3
import hashlib
import datetime
import io
import zipfile
import pdfplumber
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(page_title="MTSE AI", page_icon="🚀", layout="wide")

# ==========================================================
# STYLE
# ==========================================================

st.markdown("""
<style>
body {
    background: linear-gradient(135deg,#0f172a,#111827);
    color:white;
}
section[data-testid="stSidebar"] {
    background:#0b1120;
}
.stButton > button {
    width:100%;
    border-radius:8px;
    height:42px;
    font-weight:600;
    background:rgba(255,255,255,0.05);
    color:white;
}
.stButton > button:hover {
    background:linear-gradient(90deg,#00c6ff,#0072ff);
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# LANGUAGE
# ==========================================================

if "lang" not in st.session_state:
    st.session_state.lang = "ar"

def t(ar, en):
    return ar if st.session_state.lang == "ar" else en

# ==========================================================
# DATABASE
# ==========================================================

conn = sqlite3.connect("mtse.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT,
role TEXT,
package TEXT,
credits INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS cost_history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
project TEXT,
total REAL,
created_at TEXT
)
""")

conn.commit()

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

# Admin default
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
              ("admin",hash_pass("admin123"),"admin","enterprise",9999))
    conn.commit()

# ==========================================================
# AUTH
# ==========================================================

if "user" not in st.session_state:
    st.session_state.user = None

def login(u,p):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (u,hash_pass(p)))
    return c.fetchone()

# ==========================================================
# AI SETUP
# ==========================================================

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def ask_ai(system,user):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role":"system","content":system},
            {"role":"user","content":user}
        ],
        temperature=0.5,
        max_tokens=2000
    )
    return response.choices[0].message.content

def classify(text):
    return ask_ai("أنت مصنف محتوى محترف",
                  f"حدد نوع المحتوى: هندسي / مالي / إداري / تسويقي / قانوني / مختلط\n{text}")

# ==========================================================
# COST ENGINE
# ==========================================================

def cost_engine(base):
    return {
        "Base Cost": base,
        "Indirect 10%": base*0.10,
        "Waste 5%": base*0.05,
        "Admin 7%": base*0.07,
        "Profit 15%": base*0.15,
        "Conservative": base*1.05,
        "Moderate": base*1.15,
        "Aggressive": base*1.25
    }

# ==========================================================
# PDF REPORT
# ==========================================================

def generate_pdf(content):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("MTSE AI Professional Report",styles["Heading1"]))
    elements.append(Spacer(1,0.5*inch))
    elements.append(Paragraph(content,styles["Normal"]))
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==========================================================
# LOGIN PAGE
# ==========================================================

if not st.session_state.user:

    st.title(t("تسجيل الدخول","Login"))

    u = st.text_input(t("اسم المستخدم","Username"))
    p = st.text_input(t("كلمة المرور","Password"),type="password")

    if st.button(t("دخول","Login")):
        user = login(u,p)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error(t("بيانات غير صحيحة","Invalid credentials"))

# ==========================================================
# MAIN SYSTEM
# ==========================================================

else:

    user = st.session_state.user
    role = user[3]
    credits = user[5]

    with st.sidebar:

        st.markdown("## 🚀 MTSE AI")

        if st.button("🌍 العربية / English"):
            st.session_state.lang = "en" if st.session_state.lang=="ar" else "ar"
            st.rerun()

        page = st.radio(
            t("القائمة","Navigation"),
            [
                t("المحلل الشامل","Universal Analyzer"),
                t("محرك المقايسات","Cost Engine"),
                t("تحليل السوشيال","Social Media"),
                t("التقارير","Reports"),
                t("الإدارة","Admin"),
                t("تسجيل الخروج","Logout")
            ]
        )

        st.write(f"👤 {user[1]}")
        st.write(f"⚡ {t('الرصيد','Credits')}: {credits}")

    # ==========================================================
    # UNIVERSAL ANALYZER
    # ==========================================================

    if page == t("المحلل الشامل","Universal Analyzer"):

        text = st.text_area(t("اكتب نص","Enter text"))
        file = st.file_uploader(t("ارفع ملف","Upload file"))

        if st.button(t("تحليل","Analyze")):

            if credits <= 0:
                st.error(t("لا يوجد رصيد","No credits left"))
            else:

                combined = text if text else ""

                if file:
                    if file.name.endswith(".pdf"):
                        with pdfplumber.open(file) as pdf:
                            for pg in pdf.pages:
                                combined += pg.extract_text() or ""
                    elif file.name.endswith(".docx"):
                        doc = Document(file)
                        for para in doc.paragraphs:
                            combined += para.text
                    elif file.name.endswith(".csv"):
                        df = pd.read_csv(file)
                        combined += df.to_string()
                    elif file.name.endswith(".xlsx"):
                        df = pd.read_excel(file)
                        combined += df.to_string()
                    elif file.name.endswith(".zip"):
                        with zipfile.ZipFile(file) as z:
                            combined += "ZIP contains: " + ", ".join(z.namelist())
                    else:
                        combined += file.read().decode("utf-8",errors="ignore")

                content_type = classify(combined)
                st.subheader(t("نوع المحتوى","Content Type"))
                st.write(content_type)

                result = ask_ai(
                    "أنت محلل مشاريع شامل يقدم تقرير احترافي شامل",
                    combined
                )

                st.markdown(result)

                pdf = generate_pdf(result)
                st.download_button(t("تحميل PDF","Download PDF"),pdf,"MTSE_Report.pdf")

                c.execute("UPDATE users SET credits=credits-1 WHERE username=?",(user[1],))
                conn.commit()

    # ==========================================================
    # COST ENGINE
    # ==========================================================

    elif page == t("محرك المقايسات","Cost Engine"):

        qty = st.number_input(t("الكمية","Quantity"),0.0)
        price = st.number_input(t("سعر الوحدة","Unit Price"),0.0)

        if st.button(t("احسب","Calculate")):
            base = qty*price
            result = cost_engine(base)
            st.json(result)

            c.execute("INSERT INTO cost_history VALUES(NULL,?,?,?)",
                      ("Manual",base,str(datetime.datetime.now())))
            conn.commit()

    # ==========================================================
    # SOCIAL MEDIA
    # ==========================================================

    elif page == t("تحليل السوشيال","Social Media"):

        content = st.text_area(t("ضع الرابط أو المحتوى","Paste link or content"))

        if st.button(t("تحليل سوشيال","Analyze Social")):
            result = ask_ai(
                "أنت استراتيجي تسويق محترف يقدم تحليل أداء + خطة تطوير",
                content
            )
            st.markdown(result)

    # ==========================================================
    # REPORTS
    # ==========================================================

    elif page == t("التقارير","Reports"):

        final = st.text_area(t("محتوى التقرير","Report content"))

        if st.button(t("إنشاء تقرير","Generate Report")):
            pdf = generate_pdf(final)
            st.download_button(t("تحميل التقرير","Download Report"),
                               pdf,"MTSE_Final_Report.pdf")

    # ==========================================================
    # ADMIN
    # ==========================================================

    elif page == t("الإدارة","Admin"):

        if role != "admin":
            st.error(t("صلاحية غير متاحة","Admin only"))
        else:

            new_user = st.text_input(t("اسم مستخدم جديد","New username"))
            new_pass = st.text_input(t("كلمة المرور","Password"),type="password")
            package = st.selectbox(t("الباقة","Package"),
                                   ["free","pro","enterprise"])
            credits_new = st.number_input(t("الرصيد","Credits"),0)

            if st.button(t("إنشاء مستخدم","Create User")):
                c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                          (new_user,hash_pass(new_pass),
                           "client",package,credits_new))
                conn.commit()
                st.success(t("تم الإنشاء","Created"))

            df = pd.read_sql("SELECT username,role,package,credits FROM users",conn)
            st.dataframe(df)

    # ==========================================================
    # LOGOUT
    # ==========================================================

    elif page == t("تسجيل الخروج","Logout"):
        st.session_state.user=None
        st.rerun()
