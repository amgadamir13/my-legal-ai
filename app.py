# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import re
from datetime import datetime

# =============================================
# 1. إعدادات الواجهة (حل مشكلة التنسيق العمودي)
# =============================================
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* منع النصوص من التحول لشكل عمودي وضمان انسيابية الخط العربي */
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .stMarkdown, p, div {
        direction: rtl !important;
        text-align: right !important;
        white-space: normal !important; /* حل مشكلة النص العمودي */
        word-wrap: break-word !important;
    }

    .msg-box { 
        padding: 20px; border-radius: 12px; margin-bottom: 15px; 
        border-right: 8px solid; background-color: #f9f9f9;
        line-height: 1.6;
    }
    
    .legal { border-color: #3b82f6; }
    .psych { border-color: #8b5cf6; }
    .strat { border-color: #f59e0b; }
    
    /* تحسين شكل القائمة الجانبية */
    section[data-testid="stSidebar"] { width: 350px !important; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. وظائف المعالجة
# =============================================
def extract_pdf(file_obj):
    try:
        file_obj.seek(0)
        pdf_data = file_obj.read()
        text = ""
        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            for page in doc: text += page.get_text()
        return re.sub(r'\s+', ' ', text).strip()
    except: return ""

# =============================================
# 3. تنظيم القائمة الجانبية (Sidebar Tabs)
# =============================================
if "chat_log" not in st.session_state: 
    st.session_state.chat_log = []

with st.sidebar:
    st.title("🛡️ مركز التحكم")
    key = st.text_input("Gemini API Key:", type="password")
    
    # تنظيم الأدوات في تبويبات داخل السايدبار لمنع التكدس
    tab_settings, tab_files = st.tabs(["⚙️ الإعدادات", "📂 الملفات"])
    
    with tab_settings:
        model_choice = st.selectbox("الموديل:", ["gemini-1.5-flash", "gemini-1.5-pro"])
        if st.button("🗑️ مسح المحادثة"):
            st.session_state.chat_log = []
            st.rerun()

    with tab_files:
        v_files = st.file_uploader("📂 ملفاتنا", type=["pdf"], accept_multiple_files=True)
        o_files = st.file_uploader("⚔️ ملفات الخصم", type=["pdf"], accept_multiple_files=True)

# =============================================
# 4. الواجهة الرئيسية والتنفيذ
# =============================================
st.title("⚖️ Strategic War Room Pro")

# عرض الرسائل
for chat in st.session_state.chat_log:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b><br>{chat["content"]}</div>', unsafe_allow_html=True)

with st.form("action_form"):
    query = st.text_area("اشرح الموقف الاستراتيجي:")
    cols = st.columns(3)
    btn_L = cols[0].form_submit_button("⚖️ تحليل قانوني")
    btn_P = cols[1].form_submit_button("🧠 تحليل نفسي")
    btn_S = cols[2].form_submit_button("🧨 داهية استراتيجي")

if (btn_L or btn_P or btn_S) and key and query:
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(model_name=f"models/{model_choice}")
        
        # استخراج النصوص
        v_txt = " ".join([extract_pdf(f) for f in v_files])
        o_txt = " ".join([extract_pdf(f) for f in o_files])

        # تحديد الشخصية
        role_map = {
            btn_L: ("⚖️ المحلل القانوني", "legal", "خبير قانوني ثاقب"),
            btn_P: ("🧠 المحلل النفسي", "psych", "خبير سيكولوجي ومفاوض"),
            btn_S: ("🧨 الداهية الاستراتيجي", "strat", "عقل مدبر للخطط البديلة")
        }
        
        for btn, (label, style, role) in role_map.items():
            if btn:
                current_label, current_style, current_role = label, style, role

        prompt = f"أنت {current_role}. بياناتنا: {v_txt[:5000]}. بيانات الخصم: {o_txt[:5000]}. المطلوب: {query}. أجب بالعربية بنقاط واضحة."
        
        with st.spinner("جاري التحليل..."):
            response = model.generate_content(prompt)
            if response.text:
                st.session_state.chat_log.append({"label": current_label, "content": response.text, "style": current_style})
                st.rerun()

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
