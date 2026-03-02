import streamlit as st
import os
import google.generativeai as genai

# تحميل المفتاح من Secrets
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# اختيار موديل Gemini
model = genai.GenerativeModel("gemini-1.5-flash-latest")
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
# PREMIUM UI STYLE
# ==============================

st.markdown("""
<style>

/* Global Background */
body {
    background: linear-gradient(135deg, #0f172a, #111827);
    color: white;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0b1120;
}

/* Sidebar Buttons */
.stButton > button {
    width: 100%;
    border-radius: 10px;
    height: 42px;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.1);
    background: rgba(255,255,255,0.05);
    color: white;
    transition: 0.3s;
}

.stButton > button:hover {
    background: linear-gradient(90deg,#00c6ff,#0072ff);
    transform: scale(1.03);
    border: none;
}

/* Active Page */
.active-page {
    background: linear-gradient(90deg,#00c6ff,#0072ff);
    padding: 10px;
    border-radius: 10px;
    font-weight: 700;
    margin-bottom: 8px;
}

/* Language Button */
.lang-btn button {
    background: rgba(255,255,255,0.1) !important;
    border-radius: 20px !important;
}

/* Headers */
h1, h2, h3 {
    font-weight: 700;
    letter-spacing: 1px;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# LANGUAGE SYSTEM
# ==============================

if "lang" not in st.session_state:
    st.session_state.lang = "ar"

def t(ar, en):
    return ar if st.session_state.lang == "ar" else en

# ==============================
# PAGE STATE
# ==============================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# ==============================
# SIDEBAR
# ==============================

with st.sidebar:

    st.markdown("## 🚀 MTSE AI")
    st.markdown("---")

    # Language Toggle
    if st.session_state.lang == "ar":
        if st.button("🌍 Switch to English"):
            st.session_state.lang = "en"
            st.rerun()
    else:
        if st.button("🌍 التحويل إلى العربية"):
            st.session_state.lang = "ar"
            st.rerun()

    st.markdown("---")

    # Navigation Function
    def nav_button(page_name, ar_label, en_label):
        if st.session_state.page == page_name:
            st.markdown(
                f'<div class="active-page">🟢 {t(ar_label,en_label)}</div>',
                unsafe_allow_html=True
            )
        else:
            if st.button(t(ar_label, en_label)):
                st.session_state.page = page_name
                st.rerun()

    # Pages
    nav_button("Dashboard","لوحة التحكم","Dashboard")
    nav_button("Analytics","التحليلات","Analytics")
    nav_button("AI Engine","محرك الذكاء","AI Engine")
    nav_button("Reports","التقارير","Reports")
    nav_button("Estimator","المقايسات","Estimator")
    nav_button("Settings","الإعدادات","Settings")

# ==============================
# MAIN AREA
# ==============================

st.title(t("منصة MTSE AI الاحترافية","MTSE AI Professional Platform"))

# ------------------------------
# Dashboard
# ------------------------------

if st.session_state.page == "Dashboard":
    st.subheader(t("لوحة التحكم","Dashboard"))
    st.success(t("تم تشغيل النظام بنجاح","System initialized successfully"))

# ------------------------------
# Analytics
# ------------------------------

elif st.session_state.page == "Analytics":
    st.subheader(t("قسم التحليلات","Analytics Section"))
    st.info(t("سيتم إضافة تحليلات متقدمة هنا","Advanced analytics coming soon"))
# ----------------------------
# AI Engine
# ----------------------------

elif st.session_state.page == "AI Engine":

    st.subheader(t("محرك الذكاء الاصطناعي", "AI Engine"))

    user_input = st.text_area(
        t("اكتب طلبك هنا", "Enter your request here"),
        height=150
    )

    if st.button(t("تشغيل التحليل", "Run Analysis")):

        if user_input.strip() == "":
            st.warning(t("من فضلك أدخل نص للتحليل", "Please enter text"))
        else:
            with st.spinner(t("جاري التحليل...", "Processing...")):
                try:
                    response = model.generate_content(user_input)
                    st.success(t("تم التحليل بنجاح", "Analysis Complete"))
                    st.markdown(response.text)
                except Exception as e:
                    st.error("Error: " + str(e))
# ------------------------------
# Reports
# ------------------------------

elif st.session_state.page == "Reports":
    st.subheader(t("التقارير الاحترافية","Professional Reports"))
    st.warning(t("توليد التقارير قيد التطوير","Report generator under development"))

# ------------------------------
# Estimator
# ------------------------------

elif st.session_state.page == "Estimator":
    st.subheader(t("حساب مقايسات المشاريع","Project Cost Estimator"))
    project_value = st.number_input(t("قيمة المشروع","Project value"), min_value=0)
    percentage = st.slider(t("نسبة الربح %","Profit percentage %"),0,100,20)
    if st.button(t("احسب","Calculate")):
        profit = project_value * (percentage/100)
        st.success(f"{t('الربح المتوقع','Expected Profit')}: {profit:,.2f}")

# ------------------------------
# Settings
# ------------------------------

elif st.session_state.page == "Settings":
    st.subheader(t("الإعدادات","Settings"))
    st.write(t("إعدادات المنصة العامة","General platform settings"))
