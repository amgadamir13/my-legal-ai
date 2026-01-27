# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import re
from datetime import datetime

# =============================================
# 1. الواجهة (التنسيق الأفقي ومنع تقطع العربية)
# =============================================
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stMarkdownContainer"] p {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: pre-wrap !important;
        word-break: keep-all !important; 
        line-height: 1.8 !important;
    }
    .msg-box { padding: 25px; border-radius: 15px; margin-bottom: 20px; border-right: 12px solid; width: 100%; }
    .legal { border-color: #3b82f6; background-color: #eff6ff; }
    .psych { border-color: #8b5cf6; background-color: #f5f3ff; }
    .strat { border-color: #f59e0b; background-color: #fffbeb; }
    .stButton > button { width: 100%; border-radius: 12px; font-weight: 700; background: #1e3a8a; color: white; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. وظائف المعالجة
# =============================================
def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', text)).strip()

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
# 3. الذاكرة والتحكم (Sidebar)
# =============================================
if "chat_log" not in st.session_state: st.session_state.chat_log = []

with st.sidebar:
    st.header("🛡️ مركز القيادة")
    key = st.text_input("Gemini API Key:", type="password")
    model_choice = st.selectbox("الموديل:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    st.divider()
    v_files = st.file_uploader("📂 خزنة الأدلة", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ ملفات الخصم", type=["pdf"], accept_multiple_files=True)
    if st.button("🗑️ مسح الجلسة"): 
        st.session_state.chat_log = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

for chat in st.session_state.chat_log:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

with st.form("main_form", clear_on_submit=True):
    query = st.text_area("اشرح الموقف الحالي:")
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 استراتيجي")

# =============================================
# 4. محرك التنفيذ (نظام الـ Roles المطور)
# =============================================
if (btn_L or btn_P or btn_S) and key and query:
    try:
        genai.configure(api_key=key)
        m_id = f"models/{model_choice}" if not model_choice.startswith("models/") else model_choice
        
        # إعدادات الأمان لفتح آفاق التحليل
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}
        ]
        
        model = genai.GenerativeModel(model_name=m_id, safety_settings=safety)
        
        v_txt = "".join([extract_pdf(f) for f in v_files]) if v_files else ""
        o_txt = "".join([extract_pdf(f) for f in o_files]) if o_files else ""

        # --- تطبيق نظام الـ Roles المطور الخاص بك ---
        decision = {btn_L: "L", btn_P: "P", btn_S: "S"}
        active_btn = decision.get(True)

        role_map = {
            "L": ("⚖️ القانوني", "legal", "خبير قانوني متخصص في كشف الثغرات والتحايل"),
            "P": ("🧠 النفسي", "psych", "محلل نفسي متخصص في سيكولوجية الخصم والتفاوض"),
            "S": ("🧨 الاستراتيجي", "strat", "مخطط استراتيجي داهية يبحث عن حلول غير تقليدية")
        }
        label, style, role = role_map[active_btn]

        full_prompt = f"بصفتك {role}. أدلتنا: {v_txt[:8000]}. الخصم: {o_txt[:8000]}. الموقف: {query}. حلل بعمق وبالعربية."

        with st.spinner("⚔️ جاري التحليل..."):
            res = model.generate_content(full_prompt)
            st.session_state.chat_log.append({"label": label, "content": res.text, "style": style})
            st.rerun()
                
    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")

# =============================================
# 5. التقرير الرسمي (#Official-Findings)
# =============================================
if st.session_state.chat_log:
    st.divider()
    st.markdown('<div id="official-findings"></div>', unsafe_allow_html=True)
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    report_content = "\n".join([f"[{c['label']}]:\n{c['content']}\n" for c in st.session_state.chat_log])
    st.download_button("📥 تحميل التقرير", report_content.encode('utf-8'), file_name="Report.txt")
