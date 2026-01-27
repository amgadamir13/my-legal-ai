# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import re

# =============================================
# 1. إعدادات الواجهة (منع الحروف المقطوعة نهائياً)
# =============================================
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] p {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: pre-wrap !important;
        word-break: keep-all !important; /* الضمان النهائي ضد م-ف-ت-ا-ح */
        overflow-wrap: normal !important;
        line-height: 1.8 !important;
    }
    
    .msg-box { 
        padding: 25px; border-radius: 15px; margin-bottom: 20px; 
        border-right: 12px solid; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        width: 100% !important; display: block !important;
    }
    
    .user-style { border-color: #1e3a8a; background-color: #f8fafc; color: #1e3a8a; }
    .legal { border-color: #3b82f6; background-color: #eff6ff; color: #1e3a8a; }
    .psych { border-color: #8b5cf6; background-color: #f5f3ff; color: #2e1065; }
    .strat { border-color: #f59e0b; background-color: #fffbeb; color: #451a03; }
    
    .stButton > button { width: 100%; border-radius: 12px; font-weight: 700; background: #1e3a8a; color: white; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. وظائف معالجة النصوص والملفات
# =============================================
def normalize_arabic_text(text):
    if not text: return ""
    # تنظيف الرموز غير المرئية التي تسبب تقطع الحروف في PDF
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_text_from_pdf(file_obj):
    try:
        text = ""
        # قراءة محتوى الملف مباشرة من الذاكرة
        file_bytes = file_obj.read()
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc: 
                text += page.get_text() + " "
        return normalize_arabic_text(text)
    except Exception as e: 
        return f"خطأ في قراءة الملف: {e}"

# =============================================
# 3. واجهة المستخدم والذاكرة
# =============================================
if "chat_history" not in st.session_state: 
    st.session_state.chat_history = []

with st.sidebar:
    st.header("🛡️ الإعدادات الاستراتيجية")
    api_key = st.text_input("Gemini API Key:", type="password")
    
    model_choice = st.selectbox("الموديل المستهدف:", [
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ])
    
    st.divider()
    v_files = st.file_uploader("📂 خزنة الأدلة (Vault)", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ ملفات الخصم (Opponent)", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح الجلسة"): 
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# عرض تاريخ المحادثة
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# منطقة الإدخال
with st.form("main_form", clear_on_submit=True):
    u_query = st.text_area("اشرح الموقف أو اطلب تحليل الملفات:")
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

# =============================================
# 4. محرك التنفيذ ومعالجة الطلبات
# =============================================
if (btn_L or btn_P or btn_S) and api_key and u_query:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_choice)
        
        # قراءة النصوص من الملفات المرفوعة
        v_txt = ""
        if v_files:
            for f in v_files: v_txt += extract_text_from_pdf(f)
            
        o_txt = ""
        if o_files:
            for f in o_files: o_txt += extract_text_from_pdf(f)

        # تحديد الشخصية
        label, style, role = ("⚖️ القانوني", "legal", "خبير قانوني") if btn_L else \
                             ("🧠 النفسي", "psych", "محلل نفسي") if btn_P else \
                             ("🧨 الداهية", "strat", "استراتيجي مفاوضات")
        
        prompt = f"""
        دورك: {role}.
        سياقنا (خزنة الأدلة): {v_txt[:5000]}
        ادعاءات الخصم: {o_txt[:5000]}
        السؤال: {u_query}
        حلل الموقف بعمق وكشف التناقضات بالعربية.
        """
        
        with st.spinner("جاري استنتاج الرد الاستراتيجي..."):
            response = model.generate_content(prompt)
            st.session_state.chat_history.append({"label": label, "content": response.text, "style": style})
            st.rerun()
            
    except Exception as e:
        st.error(f"⚠️ حدث خطأ: {e}")

# =============================================
# 5. التقرير النهائي للتحميل
# =============================================
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي (#Official-Findings)")
    report_text = ""
    for c in st.session_state.chat_history:
        report_text += f"{c['label']}:\n{c['content']}\n{'-'*30}\n"
    
    st.download_button("📥 تحميل التقرير كملف نصي", report_text, file_name="War_Room_Report.txt")
