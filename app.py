# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import re
from datetime import datetime

# =============================================
# 1. إعدادات الواجهة والخطوط العربية (RTL Fix)
# =============================================
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* منع تقطع الحروف العربية وضمان العرض الأفقي */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] p {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: pre-wrap !important;
        word-break: keep-all !important; 
        overflow-wrap: normal !important;
    }
    
    .msg-box { 
        padding: 25px; border-radius: 15px; margin-bottom: 20px; 
        border-right: 12px solid; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        width: 100% !important; display: block !important;
    }
    
    .user-style { border-color: #1e3a8a; background-color: #f8fafc; color: #1e3a8a; }
    .legal { border-color: #3b82f6; background-color: #eff6ff; }
    .psych { border-color: #8b5cf6; background-color: #f5f3ff; }
    .strat { border-color: #f59e0b; background-color: #fffbeb; }
    
    /* تنسيق قسم التقرير النهائي */
    .finding-card {
        background: #ffffff; padding: 20px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. وظائف المعالجة
# =============================================
def normalize_text(text):
    if not text: return ""
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def extract_pdf_text(file_obj):
    try:
        text = ""
        with fitz.open(stream=file_obj.read(), filetype="pdf") as doc:
            for page in doc: text += page.get_text() + " "
        return normalize_text(text)
    except Exception as e: return f"Error: {e}"

# =============================================
# 3. محرك التطبيق والذاكرة
# =============================================
if "history" not in st.session_state: st.session_state.history = []

with st.sidebar:
    st.header("🛡️ الإعدادات")
    key = st.text_input("Gemini API Key:", type="password")
    model_name = st.selectbox("الموديل:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    v_files = st.file_uploader("📂 الخزنة", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ الخصم", type=["pdf"], accept_multiple_files=True)
    if st.button("🗑️ مسح"): 
        st.session_state.history = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

for chat in st.session_state.history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

with st.form("main_form", clear_on_submit=True):
    query = st.text_area("اشرح الموقف:")
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

if (btn_L or btn_P or btn_S) and key and query:
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(model_name)
        v_txt = "".join([extract_pdf_text(f) for f in v_files]) if v_files else ""
        o_txt = "".join([extract_pdf_text(f) for f in o_files]) if o_files else ""
        
        label, style, role = ("⚖️ القانوني", "legal", "محامي") if btn_L else \
                             ("🧠 النفسي", "psych", "خبير نفسي") if btn_P else \
                             ("🧨 الداهية", "strat", "استراتيجي")
        
        prompt = f"أنت {role}. سياقنا: {v_txt[:4000]}. الخصم: {o_txt[:4000]}. السؤال: {query}. أجب بالعربية."
        
        with st.spinner("جاري التحليل..."):
            res = model.generate_content(prompt)
            st.session_state.history.append({"label": label, "content": res.text, "style": style})
            st.rerun()
    except Exception as e: st.error(f"Error: {e}")

# =============================================
# 4. قسم النتائج الرسمية (#Official-Findings)
# =============================================
if st.session_state.history:
    st.divider()
    st.markdown('<div id="official-findings"></div>', unsafe_allow_html=True) # رابط الوصول السريع
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    
    report = "\n".join([f"{c['label']}: {c['content']}" for c in st.session_state.history])
    
    st.download_button(
        label="📥 تحميل التقرير الرسمي",
        data=report,
        file_name=f"Legal_Report_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )
