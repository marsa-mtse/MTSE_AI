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

# Dashboard
if st.session_state.page == "Dashboard":
    st.markdown("### 🟢 " + t("لوحة التحكم", "Dashboard"))
else:
    if st.button(t("لوحة التحكم", "Dashboard")):
        st.session_state.page = "Dashboard"
        st.rerun()

# Analytics
if st.session_state.page == "Analytics":
    st.markdown("### 🟢 " + t("التحليلات", "Analytics"))
else:
    if st.button(t("التحليلات", "Analytics")):
        st.session_state.page = "Analytics"
        st.rerun()

# AI Engine
if st.session_state.page == "AI Engine":
    st.markdown("### 🟢 " + t("محرك الذكاء", "AI Engine"))
else:
    if st.button(t("محرك الذكاء", "AI Engine")):
        st.session_state.page = "AI Engine"
        st.rerun()

# Reports
if st.session_state.page == "Reports":
    st.markdown("### 🟢 " + t("التقارير", "Reports"))
else:
    if st.button(t("التقارير", "Reports")):
        st.session_state.page = "Reports"
        st.rerun()

# Estimator
if st.session_state.page == "Estimator":
    st.markdown("### 🟢 " + t("المقايسات", "Estimator"))
else:
    if st.button(t("المقايسات", "Estimator")):
        st.session_state.page = "Estimator"
        st.rerun()

# Settings
if st.session_state.page == "Settings":
    st.markdown("### 🟢 " + t("الإعدادات", "Settings"))
else:
    if st.button(t("الإعدادات", "Settings")):
        st.session_state.page = "Settings"
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
