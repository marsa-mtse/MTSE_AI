# ==========================================================
# MTSE AI — CLEAN ENTERPRISE BUILD (AR FIXED + LANG FIXED)
# ==========================================================

import streamlit as st
from groq import Groq
import pandas as pd
import sqlite3
import hashlib
import datetime
import io
import zipfile
import pdfplumber
from docx import Document

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

import arabic_reshaper
from bidi.algorithm import get_display

# ==========================================================
# CONFIG
# ==========================================================

st.set_page_config(page_title="MTSE AI", page_icon="🚀", layout="wide")

# ==========================================================
# SESSION INIT
# ==========================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "lang" not in st.session_state:
    st.session_state.lang = "ar"

# ==========================================================
# LANGUAGE FUNCTION
# ==========================================================

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
CREATE TABLE IF NOT EXISTS analyses(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
engine TEXT,
input TEXT,
output TEXT,
created_at TEXT
)
""")

conn.commit()

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

# Default Admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
              ("admin", hash_pass("admin123"), "admin", "enterprise", 9999))
    conn.commit()

# ==========================================================
# AI SETUP
# ==========================================================

groq_key = st.secrets.get("GROQ_API_KEY", None)
client = Groq(api_key=groq_key) if groq_key else None

def ask_ai(system_prompt, user_prompt):
    if not client:
        return "Groq API not configured."
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4,
        max_tokens=2000
    )
    return response.choices[0].message.content

# ==========================================================
# PDF GENERATOR (ARABIC FIXED)
# ==========================================================

def generate_pdf(content, username):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()

    pdfmetrics.registerFont(TTFont('ArabicFont', 'Amiri-Regular.ttf'))

    arabic_style = ParagraphStyle(
        name='ArabicStyle',
        parent=styles['Normal'],
        fontName='ArabicFont',
        fontSize=12,
        leading=18,
    )

    reshaped_text = arabic_reshaper.reshape(content)
    bidi_text = get_display(reshaped_text)

    elements.append(Paragraph("MTSE AI Professional Report", styles["Heading1"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Client: {username}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(bidi_text.replace("\n", "<br/>"), arabic_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==========================================================
# LOGIN FUNCTION
# ==========================================================

def login(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_pass(password)))
    return c.fetchone()

# ==========================================================
# LOGIN PAGE
# ==========================================================

if not st.session_state.user:

    st.title("MTSE AI Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login(u, p)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid credentials")

# ==========================================================
# MAIN SYSTEM
# ==========================================================

else:

    user = st.session_state.user
    username = user[1]
    role = user[3]

    # تحديث الرصيد live
    c.execute("SELECT credits FROM users WHERE username=?", (username,))
    credits = c.fetchone()[0]

    with st.sidebar:

        st.markdown("## 🚀 MTSE AI")

        if st.button("🌍 العربية / English"):
            st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"
            st.rerun()

        page = st.radio(t("القائمة","Navigation"), [
            t("المحلل الشامل","Universal Analyzer"),
            t("محرك المقايسات","Cost Engine"),
            t("تحليل السوشيال","Social Engine"),
            t("التقارير","Reports"),
            t("الإدارة","Admin"),
            t("تسجيل الخروج","Logout")
        ])

        st.write(f"👤 {username}")
        st.write(f"⚡ {t('الرصيد','Credits')}: {credits}")

    # ======================================================
    # UNIVERSAL ANALYZER
    # ======================================================

    if page == t("المحلل الشامل","Universal Analyzer"):

        text = st.text_area(t("اكتب النص","Enter text"))
        file = st.file_uploader(t("ارفع ملف","Upload file"))

        if st.button(t("تحليل","Analyze")):

            if credits <= 0:
                st.error(t("لا يوجد رصيد","No credits left"))
            else:

                combined = text or ""

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
                        combined += file.read().decode("utf-8", errors="ignore")

                result = ask_ai(
                    "أنت محلل مشاريع محترف يقدم تقرير شامل",
                    combined[:12000]
                )

                st.markdown(result)

                c.execute("INSERT INTO analyses VALUES(NULL,?,?,?,?,?)",
                          (username, "universal", combined[:500], result,
                           datetime.datetime.now().isoformat()))

                c.execute("UPDATE users SET credits=credits-1 WHERE username=?",
                          (username,))
                conn.commit()

                pdf = generate_pdf(result, username)
                st.download_button(t("تحميل PDF","Download PDF"),
                                   pdf,
                                   "MTSE_Report.pdf")

    # ======================================================
    # COST ENGINE
    # ======================================================

    elif page == t("محرك المقايسات","Cost Engine"):

        qty = st.number_input(t("الكمية","Quantity"), 0.0)
        price = st.number_input(t("سعر الوحدة","Unit Price"), 0.0)

        if st.button(t("احسب","Calculate")):
            base = qty * price
            total = base * 1.25

            st.json({
                "Base": base,
                "Total (with margins)": total
            })

    # ======================================================
    # SOCIAL ENGINE
    # ======================================================

    elif page == t("تحليل السوشيال","Social Engine"):

        content = st.text_area(t("ضع الرابط أو المحتوى","Paste link or content"))

        if st.button(t("تحليل","Analyze")):
            result = ask_ai(
                "أنت استراتيجي تسويق محترف يقدم تحليل أداء وخطة تطوير",
                content
            )
            st.markdown(result)

    # ======================================================
    # REPORTS
    # ======================================================

    elif page == t("التقارير","Reports"):

        report_text = st.text_area(t("محتوى التقرير","Report Content"))

        if st.button(t("إنشاء تقرير","Generate Report")):
            pdf = generate_pdf(report_text, username)
            st.download_button(t("تحميل التقرير","Download Report"),
                               pdf,
                               "Final_Report.pdf")

    # ======================================================
    # ADMIN
    # ======================================================

    elif page == t("الإدارة","Admin"):

        if role != "admin":
            st.error("Admin only")
        else:

            new_user = st.text_input(t("اسم مستخدم جديد","New Username"))
            new_pass = st.text_input(t("كلمة المرور","Password"), type="password")
            new_credits = st.number_input(t("الرصيد","Credits"), 0)

            if st.button(t("إنشاء مستخدم","Create User")):
                c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                          (new_user, hash_pass(new_pass),
                           "client", "free", new_credits))
                conn.commit()
                st.success(t("تم الإنشاء","User Created"))

            df = pd.read_sql("SELECT username,role,credits FROM users", conn)
            st.dataframe(df)

    # ======================================================
    # LOGOUT
    # ======================================================

    elif page == t("تسجيل الخروج","Logout"):
        st.session_state.user = None
        st.rerun()
