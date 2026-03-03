# ==========================================================
# MTSE AI — CLEAN STABLE ENTERPRISE BUILD
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
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

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
# LANGUAGE
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

# Default admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
              ("admin", hash_pass("admin123"), "admin", "enterprise", 9999))
    conn.commit()

# ==========================================================
# AI
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
# PDF
# ==========================================================

def generate_pdf(content, username):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("MTSE AI Professional Report", styles["Heading1"]))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(f"Client: {username}", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(content.replace("\n", "<br/>"), styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==========================================================
# LOGIN
# ==========================================================

def login(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_pass(password)))
    return c.fetchone()

if not st.session_state.user:

    st.title("MTSE AI Login")

    u = st.text_input("Username", key="login_user")
    p = st.text_input("Password", type="password", key="login_pass")

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
    credits = user[5]

    with st.sidebar:

        st.markdown("## 🚀 MTSE AI")

        if st.button("🌍 Arabic / English"):
            st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"
            st.rerun()

        page = st.radio("Navigation", [
            "Universal Analyzer",
            "Cost Engine",
            "Social Engine",
            "Reports",
            "Admin",
            "Logout"
        ], key="main_nav")

        st.write(f"👤 {username}")
        st.write(f"⚡ Credits: {credits}")

    # ======================================================
    # UNIVERSAL ANALYZER
    # ======================================================

    if page == "Universal Analyzer":

        text = st.text_area("Enter Text", key="ua_text")
        file = st.file_uploader("Upload File", key="ua_file")

        if st.button("Analyze", key="ua_btn"):

            if credits <= 0:
                st.error("No credits left")
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
                st.download_button("Download PDF", pdf, "MTSE_Report.pdf")

    # ======================================================
    # COST ENGINE
    # ======================================================

    elif page == "Cost Engine":

        qty = st.number_input("Quantity", 0.0, key="cost_qty")
        price = st.number_input("Unit Price", 0.0, key="cost_price")

        if st.button("Calculate", key="cost_btn"):

            base = qty * price
            total = base * 1.25

            st.json({
                "Base": base,
                "Total (with margins)": total
            })

    # ======================================================
    # SOCIAL ENGINE
    # ======================================================

    elif page == "Social Engine":

        content = st.text_area("Paste Link or Content", key="social_text")

        if st.button("Analyze Social", key="social_btn"):

            result = ask_ai(
                "أنت استراتيجي تسويق محترف يقدم تحليل أداء وخطة تطوير",
                content
            )

            st.markdown(result)

    # ======================================================
    # REPORTS
    # ======================================================

    elif page == "Reports":

        report_text = st.text_area("Report Content", key="report_text")

        if st.button("Generate Report", key="report_btn"):
            pdf = generate_pdf(report_text, username)
            st.download_button("Download Report", pdf, "Final_Report.pdf")

    # ======================================================
    # ADMIN
    # ======================================================

    elif page == "Admin":

        if role != "admin":
            st.error("Admin only")
        else:

            new_user = st.text_input("New Username", key="admin_new_user")
            new_pass = st.text_input("Password", type="password", key="admin_new_pass")
            new_credits = st.number_input("Credits", 0, key="admin_new_credits")

            if st.button("Create User", key="admin_create"):
                c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                          (new_user, hash_pass(new_pass),
                           "client", "free", new_credits))
                conn.commit()
                st.success("User Created")

            df = pd.read_sql("SELECT username,role,credits FROM users", conn)
            st.dataframe(df)

    # ======================================================
    # LOGOUT
    # ======================================================

    elif page == "Logout":
        st.session_state.user = None
        st.rerun()
