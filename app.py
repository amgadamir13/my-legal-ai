# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import re
from datetime import datetime

# =============================================
# 1. إعدادات الواجهة (الحل الجذري للخط العربي)
# =============================================
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* فرض العرض الأفقي ومنع تقطع الحروف العربية */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] p {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: pre-wrap !important;
        word-break: keep-all !important; 
        overflow-wrap: normal !important;
        line-height: 1.8 !important;
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
    
    /* تنسيق زر التحميل وقسم النتائج الرسمية */
    .stButton > button { width: 100%; border-radius: 12px; font-weight: 700; background: #1e3a8a; color: white; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. وظائف المعالجة الذكية
# =============================================
def clean_text(text):
    if not text: return ""
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def extract_pdf(file_obj):
    try:
        file_obj.seek(0)
        pdf_data = file_obj.read()
        text = ""
        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            for page in doc: text += page.get_text() + " "
        return clean_text(text)
    except Exception as e: return f"[خطأ: {e}]"

# =============================================
# 3. الذاكرة والتحكم
# =============================================
if "chat_log" not in st.session_state: st.session_state.chat_log = []

with st.sidebar:
    st.header("🛡️ الإعدادات الاستراتيجية")
    key = st.text_input("Gemini API Key:", type="password")
    model_choice = st.selectbox("الموديل المستهدف:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    
    st.divider()
    v_files = st.file_uploader("📂 خزنة الأدلة (Vault)", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ ملفات الخصم (Opponent)", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح الجلسة"): 
        st.session_state.chat_log = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# عرض فقاعات الحوار
for chat in st.session_state.chat_log:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# منطقة الإدخال
with st.form("main_form", clear_on_submit=True):
    query = st.text_area("اشرح الموقف الحالي:")
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

# =============================================
# 4. محرك التنفيذ (Logic)
# =============================================
if (btn_L or btn_P or btn_S) and key and query:
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(model_choice)
        
        v_txt = "".join([extract_pdf(f) for f in v_files]) if v_files else ""
        o_txt = "".join([extract_pdf(f) for f in o_files]) if o_files else ""

        config = {
            btn_L: ("⚖️ القانوني", "legal", "خبير قانوني متخصص في الثغرات"),
            btn_P: ("🧠 النفسي", "psych", "محلل نفسي وخبير تفاوض"),
            btn_S: ("🧨 الداهية", "strat", "مخطط استراتيجي وداهية سياسي")
        }
        label, style, role = config[True]

        prompt = f"أنت {role}. سياقنا: {v_txt[:8000]}. الخصم: {o_txt[:8000]}. السؤال: {query}. أجب بالعربية بوضوح."
        
        with st.spinner("جاري التحليل..."):
            res = model.generate_content(prompt)
            st.session_state.chat_log.append({"label": label, "content": res.text, "style": style})
            st.rerun()
    except Exception as e: st.error(f"Error: {e}")

# =============================================
# 5. التقرير الرسمي (#Official-Findings)
# =============================================
if st.session_state.chat_log:
    st.divider()
    # إضافة المعرف الخاص بالرابط
    st.markdown('<div id="official-findings"></div>', unsafe_allow_html=True)
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    
    # تجميع النص للتحميل
    report_content = f"--- تقرير Strategic War Room ---\nالتاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    for c in st.session_state.chat_log:
        report_content += f"[{c['label']}]:\n{c['content']}\n\n"

    st.download_button(
        label="📥 تحميل التقرير الرسمي الكامل",
        data=report_content,
        file_name=f"Strategic_Report_{datetime.now().strftime('%y%m%d')}.txt",
        mime="text/plain"
    )
