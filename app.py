# ==============================================================
# MTSE AI — ENTERPRISE SINGLE FILE MASTER BUILD
# ==============================================================

import streamlit as st
from groq import Groq
import pandas as pd
import numpy as np
import sqlite3
import hashlib
import datetime
import zipfile
import io
import pdfplumber
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# ==============================================================
# CONFIG
# ==============================================================

st.set_page_config(page_title="MTSE AI", page_icon="🚀", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ==============================================================
# PREMIUM STYLE
# ==============================================================

st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0f172a, #111827);
    color: white;
}
section[data-testid="stSidebar"] {
    background: #0b1120;
}
.stButton > button {
    width: 100%;
    border-radius: 10px;
    height: 42px;
    font-weight: 600;
    background: rgba(255,255,255,0.05);
    color: white;
}
.stButton > button:hover {
    background: linear-gradient(90deg,#00c6ff,#0072ff);
}
.active-page {
    background: linear-gradient(90deg,#00c6ff,#0072ff);
    padding: 10px;
    border-radius: 10px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================
# LANGUAGE SYSTEM
# ==============================================================

if "lang" not in st.session_state:
    st.session_state.lang = "ar"

def t(ar, en):
    return ar if st.session_state.lang == "ar" else en

# ==============================================================
# DATABASE
# ==============================================================

conn = sqlite3.connect("mtse_enterprise.db", check_same_thread=False)
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

def create_admin():
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                  ("admin", hash_pass("admin123"), "admin", "enterprise", 9999))
        conn.commit()

create_admin()

# ==============================================================
# AUTH
# ==============================================================

if "user" not in st.session_state:
    st.session_state.user = None

def login(u, p):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (u, hash_pass(p)))
    return c.fetchone()

# ==============================================================
# AI CORE
# ==============================================================

def ask_ai(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],
        temperature=0.5,
        max_tokens=2000
    )
    return response.choices[0].message.content

def classify_content(text):
    return ask_ai(
        "أنت مصنف محتوى احترافي.",
        f"حدد نوع المحتوى (هندسي/مالي/إداري/تسويقي/قانوني/مختلط):\n{text}"
    )

# ==============================================================
# COST ENGINE
# ==============================================================

def calculate_cost(base):
    indirect = base * 0.10
    waste = base * 0.05
    admin = base * 0.07
    profit = base * 0.15

    return {
        "Base": base,
        "Indirect": indirect,
        "Waste": waste,
        "Admin": admin,
        "Profit": profit,
        "Conservative": base * 1.05,
        "Moderate": base * 1.15,
        "Aggressive": base * 1.25
    }

# ==============================================================
# PDF REPORT
# ==============================================================

def generate_pdf(content):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("MTSE AI Professional Report", styles["Heading1"]))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(content, styles["Normal"]))
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==============================================================
# LOGIN PAGE
# ==============================================================

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

else:

    user = st.session_state.user
    role = user[3]
    credits = user[5]

    with st.sidebar:

        st.markdown("## 🚀 MTSE AI")

        if st.button("🌍 العربية / English"):
            st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"
            st.rerun()

        page = st.radio("Navigation", [
            "Universal Analyzer",
            "Cost Engine",
            "Social Media",
            "Report",
            "Admin",
            "Logout"
        ])

        st.write(f"👤 {user[1]}")
        st.write(f"⚡ Credits: {credits}")

    # ==============================================================
    # UNIVERSAL ANALYZER
    # ==============================================================

    if page == "Universal Analyzer":

        text = st.text_area("Text Input")
        file = st.file_uploader("Upload File")

        if st.button("Analyze"):

            if credits <= 0:
                st.error("No credits left.")
            else:

                combined = text if text else ""

                if file:
                    if file.name.endswith(".pdf"):
                        with pdfplumber.open(file) as pdf:
                            for page_pdf in pdf.pages:
                                combined += page_pdf.extract_text() or ""
                    elif file.name.endswith(".docx"):
                        doc = Document(file)
                        for para in doc.paragraphs:
                            combined += para.text
                    else:
                        combined += file.read().decode("utf-8", errors="ignore")

                content_type = classify_content(combined)
                st.subheader("Content Type")
                st.write(content_type)

                result = ask_ai(
                    "أنت محلل مشاريع شامل.",
                    f"حلل المحتوى التالي تحليل كامل:\n{combined}"
                )

                st.markdown(result)

                pdf = generate_pdf(result)
                st.download_button("Download PDF", pdf, "report.pdf")

                c.execute("UPDATE users SET credits=credits-1 WHERE username=?",
                          (user[1],))
                conn.commit()

    # ==============================================================
    # COST ENGINE
    # ==============================================================

    elif page == "Cost Engine":

        qty = st.number_input("Quantity", 0.0)
        price = st.number_input("Unit Price", 0.0)

        if st.button("Calculate"):
            base = qty * price
            results = calculate_cost(base)
            st.json(results)

            c.execute("INSERT INTO cost_history VALUES(NULL,?,?,?)",
                      ("Manual Project", base, str(datetime.datetime.now())))
            conn.commit()

    # ==============================================================
    # SOCIAL MEDIA
    # ==============================================================

    elif page == "Social Media":

        link = st.text_area("Paste Social Link or Content")

        if st.button("Analyze Social"):
            result = ask_ai(
                "أنت استراتيجي سوشيال ميديا محترف.",
                f"حلل هذا الرابط أو المحتوى تحليل شامل:\n{link}"
            )
            st.markdown(result)

    # ==============================================================
    # REPORT PAGE
    # ==============================================================

    elif page == "Report":

        content = st.text_area("Final Content")

        if st.button("Generate PDF"):
            pdf = generate_pdf(content)
            st.download_button("Download Report", pdf, "MTSE_Report.pdf")

    # ==============================================================
    # ADMIN
    # ==============================================================

    elif page == "Admin":

        if role != "admin":
            st.error("Admin Only")
        else:
            new_user = st.text_input("New Username")
            new_pass = st.text_input("Password", type="password")
            package = st.selectbox("Package", ["free","pro","enterprise"])
            credits_new = st.number_input("Credits", 0)

            if st.button("Create User"):
                c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                          (new_user, hash_pass(new_pass), "client",
                           package, credits_new))
                conn.commit()
                st.success("User Created")

            st.subheader("All Users")
            df = pd.read_sql("SELECT username,role,package,credits FROM users", conn)
            st.dataframe(df)

    # ==============================================================
    # LOGOUT
    # ==============================================================

    elif page == "Logout":
        st.session_state.user = None
        st.rerun()
