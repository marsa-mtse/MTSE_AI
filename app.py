import streamlit as st
from groq import Groq
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import numpy as np

# ==============================
# PAGE CONFIG
# ==============================

st.set_page_config(
    page_title="MTSE AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# GROQ CONFIG
# ==============================

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def ask_ai(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """
أنت نظام ذكاء تحليلي شامل.
تحلل أي محتوى (مشاريع - ملفات - سوشيال ميديا - جداول - تقارير).
استخدم تحليل متعدد الطبقات يشمل:

- ملخص تنفيذي
- تحليل هيكلي
- تحليل مالي (لو يوجد أرقام)
- كشف المخاطر
- نقاط القوة والضعف
- فرص التحسين
- توصيات استراتيجية
- الخلاصة النهائية
"""
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"حدث خطأ: {e}"

# ==============================
# STYLE
# ==============================

st.markdown("""
<style>
body {background: linear-gradient(135deg, #0f172a, #111827);color: white;}
section[data-testid="stSidebar"] {background: #0b1120;}
.stButton > button {
    width:100%;border-radius:10px;height:42px;font-weight:600;
    background:rgba(255,255,255,0.05);color:white;
}
.stButton > button:hover {
    background:linear-gradient(90deg,#00c6ff,#0072ff);
}
.active-page {
    background:linear-gradient(90deg,#00c6ff,#0072ff);
    padding:10px;border-radius:10px;font-weight:700;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# STATE
# ==============================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "items" not in st.session_state:
    st.session_state.items = []

# ==============================
# SIDEBAR
# ==============================

with st.sidebar:
    st.markdown("## 🚀 MTSE AI")
    st.markdown("---")

    pages = ["Dashboard","AI Engine","Estimator","Comparison","Analytics","Reports","Settings"]

    for p in pages:
        if st.session_state.page == p:
            st.markdown(f'<div class="active-page">🟢 {p}</div>', unsafe_allow_html=True)
        else:
            if st.button(p):
                st.session_state.page = p
                st.rerun()

# ==============================
# TITLE
# ==============================

st.title("MTSE AI Enterprise Intelligence System")

# ==============================
# AI ENGINE (Universal Analyzer)
# ==============================

if st.session_state.page == "AI Engine":

    st.subheader("🤖 Universal Multi-Source Analyzer")

    text_input = st.text_area("أدخل نص للتحليل")
    uploaded_file = st.file_uploader("رفع ملف", type=["txt","csv","xlsx"])
    url_input = st.text_input("رابط موقع أو سوشيال")

    if st.button("🚀 تحليل شامل"):

        combined = ""

        if text_input:
            combined += f"\nنص:\n{text_input}\n"

        if uploaded_file:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
                combined += f"\nجدول بيانات:\n{df.head().to_string()}\n"

                # Data Intelligence
                combined += "\nتحليل إحصائي:\n"
                combined += str(df.describe())

                # Anomaly Detection
                if len(df.select_dtypes(include=np.number).columns) > 0:
                    numeric_df = df.select_dtypes(include=np.number)
                    z_scores = (numeric_df - numeric_df.mean()) / numeric_df.std()
                    if (abs(z_scores) > 3).any().any():
                        combined += "\n⚠️ تم اكتشاف قيم شاذة محتملة.\n"

            else:
                combined += uploaded_file.read().decode("utf-8", errors="ignore")

        if url_input:
            try:
                r = requests.get(url_input)
                soup = BeautifulSoup(r.text, "html.parser")
                combined += "\nمحتوى رابط:\n"
                combined += soup.get_text()[:4000]

                combined += "\n\nتحليل سوشيال ميديا إن وجد:\n"
                combined += """
قم بتحليل:
- نوع المحتوى
- الجمهور المستهدف
- قوة العلامة
- معدل التفاعل المحتمل
- خطة تحسين المحتوى
"""
            except:
                combined += "\nتعذر تحليل الرابط.\n"

        if combined.strip() == "":
            st.warning("أدخل بيانات أولاً")
        else:
            with st.spinner("تحليل متعدد الطبقات جاري..."):
                result = ask_ai(combined)
            st.markdown(result)

# ==============================
# ESTIMATOR ADVANCED
# ==============================

elif st.session_state.page == "Estimator":

    st.subheader("💰 Advanced Cost Engine")

    with st.form("add_item"):
        name = st.text_input("اسم البند")
        qty = st.number_input("الكمية", min_value=0.0)
        price = st.number_input("سعر الوحدة", min_value=0.0)
        submitted = st.form_submit_button("إضافة")

        if submitted:
            st.session_state.items.append({
                "البند": name,
                "الكمية": qty,
                "سعر الوحدة": price,
                "الإجمالي": qty * price
            })

    if st.session_state.items:
        df = pd.DataFrame(st.session_state.items)
        st.dataframe(df)

        base = df["الإجمالي"].sum()

        waste = st.slider("هالك %",0,20,5)
        overhead = st.slider("إدارة %",0,30,10)
        profit = st.slider("ربح %",0,50,20)

        conservative = base * 1.05
        moderate = base * 1.15
        aggressive = base * 1.25

        final = base * (1 + waste/100 + overhead/100 + profit/100)

        st.success(f"التكلفة النهائية: {final:,.2f}")
        st.info(f"سيناريو محافظ: {conservative:,.2f}")
        st.info(f"سيناريو متوسط: {moderate:,.2f}")
        st.info(f"سيناريو مرتفع: {aggressive:,.2f}")

# ==============================
# COMPARISON ENGINE
# ==============================

elif st.session_state.page == "Comparison":

    st.subheader("⚖️ مقارنة بين محتويين")

    text1 = st.text_area("المحتوى الأول")
    text2 = st.text_area("المحتوى الثاني")

    if st.button("قارن"):
        prompt = f"""
قارن بين المحتويين التاليين من حيث:
- نقاط القوة
- نقاط الضعف
- الفروق الاستراتيجية
- الأفضل ولماذا

المحتوى الأول:
{text1}

المحتوى الثاني:
{text2}
"""
        result = ask_ai(prompt)
        st.markdown(result)

# ==============================
# ANALYTICS
# ==============================

elif st.session_state.page == "Analytics":
    st.subheader("📊 Advanced Analytics")
    st.info("سيتم إضافة مؤشرات أداء ديناميكية")

# ==============================
# REPORTS
# ==============================

elif st.session_state.page == "Reports":
    st.subheader("📄 Professional Report Generator")
    st.info("سيتم إضافة توليد PDF وWord")

# ==============================
# SETTINGS
# ==============================

elif st.session_state.page == "Settings":
    st.subheader("⚙️ Settings")
    st.write("إعدادات النظام")
