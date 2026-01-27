# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import re
from datetime import datetime

# =============================================
# 1. إعدادات الواجهة (تنسيق بصري مريح ومنظم)
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
        line-height: 1.8 !important;
    }
    
    .msg-box { 
        padding: 20px; border-radius: 12px; margin-bottom: 15px; 
        border-right: 8px solid; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .legal { border-color: #3b82f6; background-color: #eff6ff; color: #1e3a8a; }
    .psych { border-color: #8b5cf6; background-color: #f5f3ff; color: #2e1065; }
    .strat { border-color: #f59e0b; background-color: #fffbeb; color: #451a03; }
    
    .stButton > button { width: 100%; border-radius: 10px; font-weight: 700; height: 3em; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. وظائف المعالجة التقنية
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
# 3. إدارة الجلسة والقائمة الجانبية
# =============================================
if "chat_log" not in st.session_state: 
    st.session_state.chat_log = []

with st.sidebar:
    st.header("🛡️ مركز القيادة")
    key = st.text_input("Gemini API Key:", type="password")
    
    # تحديث الأسماء لتجنب خطأ 404
    model_choice = st.selectbox("اختر الموديل:", [
        "gemini-1.5-flash", 
        "gemini-1.5-pro", 
        "gemini-1.0-pro"
    ])
    
    st.divider()
    v_files = st.file_uploader("📂 خزنة الأدلة (Vault)", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ ملفات الخصم (Opponent)", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح الجلسة"): 
        st.session_state.chat_log = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# عرض المحادثات السابقة بشكل منظم
for chat in st.session_state.chat_log:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# =============================================
# 4. محرك التنفيذ والاستجابة
# =============================================
with st.form("main_form", clear_on_submit=True):
    query = st.text_area("ادخل استفسارك الاستراتيجي هنا:")
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ تحليل قانوني")
    with c2: btn_P = st.form_submit_button("🧠 تحليل نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية استراتيجي")

if (btn_L or btn_P or btn_S) and key and query:
    try:
        genai.configure(api_key=key)
        
        # الإصلاح الجذري: التأكد من صياغة اسم الموديل بشكل يقبله الـ API
        target_model = f"models/{model_choice}" if not model_choice.startswith("models/") else model_choice
        model = genai.GenerativeModel(model_name=target_model)
        
        # معالجة الملفات
        v_txt = "".join([extract_pdf(f) for f in v_files]) if v_files else "لا توجد مستندات لنا."
        o_txt = "".join([extract_pdf(f) for f in o_files]) if o_files else "لا توجد مستندات للخصم."

        # تحديد الشخصية
        if btn_L:
            label, style, role = "⚖️ المحلل القانوني", "legal", "خبير قانوني ثاقب"
        elif btn_P:
            label, style, role = "🧠 المحلل النفسي", "psych", "خبير سيكولوجي ومفاوض"
        else:
            label, style, role = "🧨 الداهية الاستراتيجي", "strat", "عقل مدبر للخطط البديلة"

        prompt = f"""
        الرداء المهني: {role}.
        بياناتنا المتاحة: {v_txt[:8000]}
        بيانات الخصم المتاحة: {o_txt[:8000]}
        السؤال/المهمة: {query}
        
        المطلوب: إجابة عربية احترافية، مرتبة في نقاط، تركز على الحلول العملية المباشرة.
        """
        
        with st.spinner("⚔️ جاري استحضار الذكاء الاستراتيجي..."):
            res = model.generate_content(prompt)
            if res.text:
                st.session_state.chat_log.append({"label": label, "content": res.text, "style": style})
                st.rerun()
                
    except Exception as e:
        st.error(f"⚠️ خطأ تقني: {e}")

# =============================================
# 5. تصدير التقارير
# =============================================
if st.session_state.chat_log:
    st.divider()
    report_content = f"--- تقرير غرفة العمليات ---\nالتاريخ: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    for c in st.session_state.chat_log:
        report_content += f"[{c['label']}]:\n{c['content']}\n\n"

    st.download_button(
        label="📥 تحميل التقرير الاستراتيجي",
        data=report_content.encode('utf-8'),
        file_name="Strategic_Report.txt",
        mime="text/plain"
    )
