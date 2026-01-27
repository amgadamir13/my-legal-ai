# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions as gapi_errors
import fitz  # PyMuPDF
import re
from datetime import datetime

# =============================================
# 1. إعدادات الواجهة والجماليات
# =============================================
st.set_page_config(page_title="Strategic War Room Pro 2026", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important; text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    .msg-box { 
        padding: 20px; border-radius: 15px; margin-bottom: 20px; 
        border-right: 10px solid; background-color: #ffffff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .legal { border-color: #1d4ed8; background-color: #eff6ff; }
    .psych { border-color: #7c3aed; background-color: #f5f3ff; }
    .strat { border-color: #ea580c; background-color: #fffbeb; }
    .stButton > button { width: 100%; border-radius: 10px; font-weight: 700; height: 3.5em; background: #1e293b; color: white; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. وظائف المعالجة
# =============================================
def extract_pdf_clean(file_obj):
    try:
        file_obj.seek(0)
        pdf_data = file_obj.read()
        text = ""
        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            for page in doc: text += page.get_text() + " "
        return re.sub(r'\s+', ' ', text).strip()
    except: return ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =============================================
# 3. الشريط الجانبي (مركز التحكم في الحصة)
# =============================================
with st.sidebar:
    st.header("🛡️ مركز القيادة")
    api_key = st.text_input("Gemini API Key:", type="password")
    
    # خيار الموديل (تبديل الموديلات لتجاوز الكوتا)
    model_choice = st.selectbox("اختر الموديل:", ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"])
    
    # ميزة التحكم في حجم النص لتوفير الـ Tokens
    max_chars = st.slider("🔧 حد النص للملفات (لتوفير الحصة):", 500, 8000, 2000, step=500)
    
    st.divider()
    v_files = st.file_uploader("📂 ملفاتنا", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ ملفات الخصم", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح الجلسة"):
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# عرض السجل
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# =============================================
# 4. محرك التنفيذ المطور
# =============================================
with st.container():
    query = st.text_area("اشرح الموقف الاستراتيجي:")
    c1, c2, c3 = st.columns(3)
    btn_L = c1.button("⚖️ تحليل قانوني")
    btn_P = c2.button("🧠 تحليل نفسي")
    btn_S = c3.button("🧨 داهية استراتيجي")

if (btn_L or btn_P or btn_S) and api_key and query:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_choice)
        
        with st.spinner("⚔️ جاري التحليل..."):
            v_txt = " ".join([extract_pdf_clean(f) for f in v_files])
            o_txt = " ".join([extract_pdf_clean(f) for f in o_files])

            if btn_L: label, style, role = "⚖️ المحلل القانوني", "legal", "خبير قانوني ثاقب"
            elif btn_P: label, style, role = "🧠 المحلل النفسي", "psych", "خبير سيكولوجي ومفاوض"
            else: label, style, role = "🧨 الداهية الاستراتيجي", "strat", "عقل مدبر للخطط البديلة"

            # استخدام متغير max_chars للتحكم في الاستهلاك
            prompt = f"بصفتك {role}: ملفاتنا: {v_txt[:max_chars]}. الخصم: {o_txt[:max_chars]}. المهمة: {query}. أجب بالعربية."
            
            response = model.generate_content(prompt)
            if response.text:
                st.session_state.chat_history.append({"label": label, "content": response.text, "style": style})
                st.rerun()

    except gapi_errors.ResourceExhausted:
        st.error("⚠️ **انتهت حصتك المجانية حالياً.**")
        st.warning("نصيحة: قم بتقليل 'حد النص' من الشريط الجانبي أو انتظر دقيقة واحدة.")
    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
