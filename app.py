import streamlit as st
from groq import Groq
import pandas as pd
import numpy as np
import sqlite3
import zipfile
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import hashlib
import datetime

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="MTSE AI SaaS", page_icon="🚀", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("mtse_saas.db", check_same_thread=False)
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
CREATE TABLE IF NOT EXISTS estimates(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user TEXT,
project TEXT,
total REAL
)
""")

conn.commit()

# =========================
# SECURITY
# =========================

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin():
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users(username,password,role,package,credits) VALUES (?,?,?,?,?)",
                  ("admin", hash_pass("admin123"), "admin", "enterprise", 9999))
        conn.commit()

create_admin()

# =========================
# AUTH
# =========================

if "user" not in st.session_state:
    st.session_state.user = None

def login(username, password):
    hashed = hash_pass(password)
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed))
    return c.fetchone()

# =========================
# AI ENGINE
# =========================

def ask_ai(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role":"system","content":"أنت نظام ذكاء تحليلي شامل للمشاريع والسوشيال ميديا والملفات."},
            {"role":"user","content":prompt}
        ],
        temperature=0.6,
        max_tokens=2000
    )
    return response.choices[0].message.content

# =========================
# PDF
# =========================

def generate_pdf(content):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("MTSE AI Official Report", styles["Heading1"]))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(content, styles["Normal"]))
    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================
# LOGIN PAGE
# =========================

if not st.session_state.user:

    st.title("MTSE AI Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login(username, password)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid credentials")

else:

    user_data = st.session_state.user
    role = user_data[3]
    package = user_data[4]
    credits = user_data[5]

    st.sidebar.write(f"👤 {user_data[1]}")
    st.sidebar.write(f"📦 {package}")
    st.sidebar.write(f"⚡ Credits: {credits}")

    page = st.sidebar.radio("Navigation", [
        "Dashboard",
        "Universal AI",
        "Estimator",
        "Comparison",
        "Users (Admin)",
        "Logout"
    ])

    # =========================
    # DASHBOARD
    # =========================

    if page == "Dashboard":
        st.success("System Running - SaaS Mode Active")

    # =========================
    # UNIVERSAL AI
    # =========================

    elif page == "Universal AI":

        st.header("Universal AI Engine")

        text = st.text_area("Text Input")
        file = st.file_uploader("Upload File (csv/xlsx/txt/zip)")

        if st.button("Analyze"):

            if credits <= 0:
                st.error("No credits remaining.")
            else:
                combined = text if text else ""

                if file:
                    if file.name.endswith(".csv"):
                        df = pd.read_csv(file)
                        combined += df.head().to_string()
                    elif file.name.endswith(".xlsx"):
                        df = pd.read_excel(file)
                        combined += df.head().to_string()
                    elif file.name.endswith(".zip"):
                        with zipfile.ZipFile(file, "r") as zip_ref:
                            for name in zip_ref.namelist():
                                with zip_ref.open(name) as f:
                                    try:
                                        combined += f.read().decode("utf-8")
                                    except:
                                        pass
                    else:
                        combined += file.read().decode("utf-8", errors="ignore")

                result = ask_ai(combined)
                st.markdown(result)

                pdf = generate_pdf(result)
                st.download_button("Download PDF", pdf, "report.pdf")

                c.execute("UPDATE users SET credits=credits-1 WHERE username=?", (user_data[1],))
                conn.commit()

    # =========================
    # ESTIMATOR
    # =========================

    elif page == "Estimator":

        st.header("Cost Engine")

        project = st.text_input("Project Name")
        qty = st.number_input("Quantity", 0.0)
        price = st.number_input("Unit Price", 0.0)

        if st.button("Calculate & Save"):
            total = qty * price
            st.success(f"Total: {total}")
            c.execute("INSERT INTO estimates(user,project,total) VALUES (?,?,?)",
                      (user_data[1], project, total))
            conn.commit()

        st.subheader("My Estimates")
        df = pd.read_sql(f"SELECT * FROM estimates WHERE user='{user_data[1]}'", conn)
        st.dataframe(df)

    # =========================
    # COMPARISON
    # =========================

    elif page == "Comparison":

        t1 = st.text_area("First Content")
        t2 = st.text_area("Second Content")

        if st.button("Compare"):
            result = ask_ai(f"قارن بين:\n{t1}\n\nو\n{t2}")
            st.markdown(result)

    # =========================
    # ADMIN USERS
    # =========================

    elif page == "Users (Admin)":

        if role != "admin":
            st.error("Admin only.")
        else:
            st.header("User Management")

            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            new_package = st.selectbox("Package", ["free","pro","enterprise"])
            credits_amount = st.number_input("Credits", 0)

            if st.button("Create User"):
                c.execute("INSERT INTO users(username,password,role,package,credits) VALUES (?,?,?,?,?)",
                          (new_user, hash_pass(new_pass), "client", new_package, credits_amount))
                conn.commit()
                st.success("User Created")

            st.subheader("All Users")
            df = pd.read_sql("SELECT username,role,package,credits FROM users", conn)
            st.dataframe(df)

    # =========================
    # LOGOUT
    # =========================

    elif page == "Logout":
        st.session_state.user = None
        st.rerun()
