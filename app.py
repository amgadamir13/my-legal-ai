# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import io
import os
import time
import re
from datetime import datetime

# =============================================
# 1. PAGE CONFIGURATION & ENHANCED STYLING
# =============================================
st.set_page_config(
    page_title="Strategic War Room Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# التنسيق الشامل لحل مشكلة الحروف العربية (بناءً على طلبك لمنع التقطع)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] p {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: pre-wrap !important;
        word-break: keep-all !important; /* السر في بقاء الحروف متصلة */
    }
    
    .msg-box { 
        padding: 25px; border-radius: 18px; margin-bottom: 25px; line-height: 1.8; 
        border-right: 12px solid; box-shadow: 0 6px 20px rgba(0,0,0,0.1); 
        width: 100% !important; display: block !important;
    }
    
    .user-style { border-color: #1e3a8a; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #1e3a8a; }
    .legal { border-color: #3b82f6; background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); }
    .psych { border-color: #8b5cf6; background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%); }
    .strat { border-color: #f59e0b; background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); }
    
    .stButton > button { width: 100%; border-radius: 12px; font-weight: 700; background: #1e3a8a; color: white; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. ENHANCED FUNCTIONS (FROM YOUR CODE)
# =============================================

@st.cache_data(show_spinner=False)
def normalize_arabic_text(text: str) -> str:
    if not text: return ""
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', text)
    replacements = {'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ة': 'ه'}
    for old, new in replacements.items(): text = text.replace(old, new)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def validate_pdf_file(file):
    if file.type != "application/pdf": return False, "الملف ليس بصيغة PDF"
    if file.size > 10 * 1024 * 1024: return False, "حجم الملف كبير جداً (الحد الأقصى 10MB)"
    return True, ""

def extract_text_from_pdf(file_bytes):
    try:
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc: text += page.get_text() + "\n"
        return normalize_arabic_text(text)
    except Exception as e: return f"خطأ: {e}"

# =============================================
# 3. PROMPT TEMPLATES (YOUR CONDENSED BRAIN)
# =============================================
PROMPT_TEMPLATES = {
    "legal": "أنت خبير قانوني محترف. حلل الموقف التالي:\nحقائقنا: {v}\nادعاءات الخصم: {o}\nالسؤال: {q}\nالمطلوب: تقييم قانوني دقيق وتوصيات عملية.",
    "psychological": "أنت خبير في علم النفس القانوني. حلل الموقف:\nحقائقنا: {v}\nادعاءات الخصم: {o}\nالسؤال: {q}\nالمطلوب: كشف الدوافع ونقاط الضغط النفسي.",
    "strategic": "أنت استراتيجي داهية. طور خطة تكتيكية:\nحقائقنا: {v}\nادعاءات الخصم: {o}\nالهدف: {q}\nالمطلوب: خطوات غير متوقعة وسيناريوهات طوارئ."
}

# =============================================
# 4. SESSION STATE & SIDEBAR
# =============================================
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "analysis_count" not in st.session_state: st.session_state.analysis_count = 0

with st.sidebar:
    st.header("🛡️ مركز العمليات")
    api_key = st.text_input("مفتاح API:", type="password")
    model_name = st.selectbox("الموديل:", ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"])
    
    st.divider()
    v_files = st.file_uploader("📂 الخزنة", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ الخصم", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ تفريغ الذاكرة"):
        st.session_state.chat_history = []
        st.rerun()

# =============================================
# 5. MAIN INTERFACE
# =============================================
st.title("⚖️ Strategic War Room Pro")

# عرض السجل التاريخي
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>: {chat["content"]}</div>', unsafe_allow_html=True)

# استمارة التحليل
with st.form("main_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف بالتفصيل:")
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 استراتيجي")

# =============================================
# 6. EXECUTION LOGIC
# =============================================
if (btn_L or btn_P or btn_S) and api_key and user_query:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # معالجة الملفات
        v_txt = ""
        if v_files:
            for f in v_files:
                valid, msg = validate_pdf_file(f)
                if valid: v_txt += extract_text_from_pdf(f.read())
        
        o_txt = ""
        if o_files:
            for f in o_files:
                valid, msg = validate_pdf_file(f)
                if valid: o_txt += extract_text_from_pdf(f.read())

        # اختيار القالب
        a_type = "legal" if btn_L else "psychological" if btn_P else "strategic"
        label = "⚖️ القانوني" if btn_L else "🧠 النفسي" if btn_P else "🧨 الداهية"
        style = "legal" if btn_L else "psych" if btn_P else "strat"
        
        prompt = PROMPT_TEMPLATES[a_type].format(v=v_txt[:4000], o=o_txt[:4000], q=user_query)

        with st.spinner("جاري التحليل المعمق..."):
            response = model.generate_content(prompt)
            st.session_state.chat_history.append({"label": label, "content": response.text, "style": style})
            st.session_state.analysis_count += 1
            st.rerun()
            
    except Exception as e:
        st.error(f"Error: {e}")

# =============================================
# 7. OFFICIAL FINDINGS
# =============================================
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي (#Official-Findings)")
    st.download_button("📥 تحميل التقرير النهائي", 
                       "\n".join([f"{c['label']}: {c['content']}" for c in st.session_state.chat_history]),
                       file_name="strategic_report.txt")
