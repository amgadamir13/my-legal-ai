# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import io
import os
import re
from datetime import datetime

# =============================================
# 1. PAGE CONFIG & RADICAL ARABIC FIX
# =============================================
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

# حل نهائي لمشكلة تقطع الحروف وظهورها عمودياً
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* توسيع الحاوية الرئيسية لمنع تكدس النص */
    .main .block-container {
        max-width: 98% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* إصلاح الفقاعات: منع انكسار الكلمة وفرض الاتصال العرضي */
    [data-testid="stMarkdownContainer"] p, .msg-box {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: pre-wrap !important; /* يحافظ على التنسيق كما هو */
        word-break: keep-all !important; /* يمنع كسر الكلمة الواحدة نهائياً */
        overflow-wrap: normal !important; /* يمنع الالتفاف المفاجئ */
        line-height: 1.8 !important;
        display: block !important;
        width: 100% !important;
    }
    
    .msg-box { 
        padding: 25px; border-radius: 15px; margin-bottom: 20px; 
        border-right: 12px solid; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .user-style { border-color: #1e3a8a; background-color: #f8fafc; color: #1e3a8a; }
    .legal { border-color: #3b82f6; background-color: #eff6ff; color: #1e3a8a; }
    .psych { border-color: #8b5cf6; background-color: #f5f3ff; color: #2e1065; }
    .strat { border-color: #f59e0b; background-color: #fffbeb; color: #451a03; }

    /* تحسين العرض على شاشات الجوال */
    @media (max-width: 640px) {
        .msg-box { padding: 15px; font-size: 14px; }
    }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. CORE FUNCTIONS
# =============================================
def normalize_arabic_text(text):
    if not text: return ""
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_text_from_pdf(file_bytes):
    try:
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc: text += page.get_text() + " "
        return normalize_arabic_text(text)
    except Exception as e: return f"خطأ: {e}"

# =============================================
# 3. INTERFACE & SESSION STATE
# =============================================
if "chat_history" not in st.session_state: st.session_state.chat_history = []

with st.sidebar:
    st.header("🛡️ مركز التحكم")
    api_key = st.text_input("Gemini API Key:", type="password")
    
    # تم تحديث القائمة لموديلات أكثر استقراراً
    model_choice = st.selectbox("الموديل المستقر:", [
        "gemini-1.5-flash-latest", 
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash"
    ])
    
    v_files = st.file_uploader("📂 الخزنة (أوراقنا)", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ الخصم (أوراقه)", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح الجلسة"): 
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# عرض المحادثة
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# نموذج الإدخال
with st.form("main_war_form", clear_on_submit=True):
    u_query = st.text_area("اشرح الموقف أو أرفق رسالة الخصم هنا:")
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

# =============================================
# 4. AI EXECUTION LOGIC (FIXED MODEL CALL)
# =============================================
if (btn_L or btn_P or btn_S) and api_key and u_query:
    try:
        genai.configure(api_key=api_key)
        # استخدام الموديل المختار من القائمة الجانبية
        model = genai.GenerativeModel(model_choice)
        
        v_txt = "".join([extract_text_from_pdf(f.read()) for f in v_files]) if v_files else ""
        o_txt = "".join([extract_text_from_pdf(f.read()) for f in o_files]) if o_files else ""

        label, style, role = ("⚖️ القانوني", "legal", "محامي جنائي") if btn_L else \
                             ("🧠 النفسي", "psych", "خبير علم نفس جنائي") if btn_P else \
                             ("🧨 الداهية", "strat", "استراتيجي مفاوضات")
        
        prompt = f"""
        أنت الآن بدور: {role}. 
        سياقنا: {v_txt[:5000]}
        سياق الخصم: {o_txt[:5000]}
        الموقف المطلوب تحليله: {u_query}
        أجب بالعربية الفصحى، وبشكل منظم جداً، وتأكد من كشف أي تناقض بين السياقين.
        """
        
        with st.spinner("جاري التحليل الاستراتيجي..."):
            res = model.generate_content(prompt)
            st.session_state.chat_history.append({"label": label, "content": res.text, "style": style})
            st.rerun()
            
    except Exception as e:
        st.error(f"خطأ في الموديل: {e}. حاول تغيير اسم الموديل من القائمة الجانبية.")

# =============================================
# 5. OFFICIAL FINDINGS SECTION
# =============================================
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي الموحد (#Official-Findings)")
    
    report_text = "\n".join([f"{c['label']}: {c['content']}" for c in st.session_state.chat_history])
    
    st.download_button(
        label="📥 تحميل التقرير النهائي (Text)",
        data=report_text,
        file_name=f"Legal_Report_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )
