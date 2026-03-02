# ==================================================
# MTSE AI - Professional Core Structure
# Version 2026 Enterprise Architecture
# ==================================================

import streamlit as st
# ==============================
# PREMIUM UI STYLE
# ==============================

st.markdown("""
<style>

/* ===== Global Font & Background ===== */
body {
    background: linear-gradient(135deg, #0f172a, #111827);
    color: white;
}

/* ===== Sidebar ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1120, #111827);
    width: 300px !important;
    padding-top: 20px;
}
    background-color: #0b1120;
}

/* ===== Buttons ===== */
.stButton>button {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    border-radius: 8px;
    border: none;
    height: 45px;
    font-weight: 600;
}

.stButton>button:hover {
    transform: scale(1.03);
    transition: 0.2s ease-in-out;
}

/* ===== RTL Support ===== */
html[lang="ar"] body {
    direction: rtl;
    text-align: right;
}

/* ===== Headers ===== */
h1, h2, h3 {
    font-weight: 700;
    letter-spacing: 1px;
}

</style>
""", unsafe_allow_html=True)

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
# LANGUAGE SYSTEM (GLOBAL)
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
# SIDEBAR NAVIGATION
# ==============================

with st.sidebar:
    st.markdown("## 🚀 MTSE AI")
    st.markdown("---")

    # Language Toggle
    # Professional Language Switch
current_lang = st.session_state.lang

if current_lang == "ar":
    if st.button("🌍 Switch to English"):
        st.session_state.lang = "en"
        st.rerun()
else:
    if st.button("🌍 التحويل إلى العربية"):
        st.session_state.lang = "ar"
        st.rerun()


  # =============================
# Navigation Buttons (Pro Active Style)
# =============================
/* ===== Active Sidebar Button ===== */
.active-btn {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white !important;
    padding: 8px;
    border-radius: 8px;
    font-weight: 600;
    margin-bottom: 6px;
}
# ==============================
# PROFESSIONAL SIDEBAR NAVIGATION
# ==============================

pages = {
    "Dashboard": ("لوحة التحكم", "Dashboard"),
    "Analytics": ("التحليلات", "Analytics"),
    "AI Engine": ("محرك الذكاء", "AI Engine"),
    "Reports": ("التقارير", "Reports"),
    "Estimator": ("المقايسات", "Estimator"),
    "Settings": ("الإعدادات", "Settings"),
}

for page_key, (ar, en) in pages.items():

    if st.session_state.page == page_key:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg,#00c6ff,#0072ff);
                padding:10px;
                border-radius:10px;
                margin-bottom:8px;
                font-weight:600;
            ">
            🟢 {t(ar,en)}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        if st.button(t(ar,en)):
            st.session_state.page = page_key
            st.rerun()
# ==============================
# MAIN AREA ROUTER
# ==============================

st.title(t("منصة MTSE AI الاحترافية", "MTSE AI Professional Platform"))

page = st.session_state.page

if page == "Dashboard":
    st.header(t("لوحة التحكم", "Dashboard"))
    st.info(t("مرحلة البناء الأساسية جاهزة.", "Core structure initialized."))

elif page == "Analytics":
    st.header(t("التحليلات", "Analytics"))
    st.info(t("سيتم إضافة محرك التحليل المتقدم هنا.", "Advanced analytics engine will be here."))

elif page == "AI Engine":
    st.header(t("محرك الذكاء الاصطناعي", "AI Engine"))
    st.info(t("طبقة الذكاء قيد البناء.", "AI Layer under construction."))

elif page == "Reports":
    st.header(t("إدارة التقارير", "Reports Management"))
    st.info(t("نظام التقارير الاحترافي سيتم ربطه هنا.", "Professional reporting system will be connected here."))

elif page == "Estimator":
    st.header(t("نظام المقايسات الذكي", "Smart Project Estimator"))
    st.info(t("سيتم إضافة نظام المقايسات الاحترافي هنا.", "Smart estimation system will be implemented here."))

elif page == "Settings":
    st.header(t("الإعدادات", "Settings"))
    st.info(t("إعدادات المنصة والتحكم الكامل.", "Platform settings and control."))
