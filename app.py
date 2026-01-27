# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import re
from datetime import datetime

# =============================================
# 1. إعدادات الواجهة (منع التنسيق العمودي نهائياً)
# =============================================
st.set_page_config(page_title="Strategic War Room Pro 2026", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* حل مشكلة النص العمودي: فرض الانسياب الأفقي */
    .stMarkdown, p, div, [data-testid="stMarkdownContainer"] {
        direction: rtl !important;
        text-align: right !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        display: block !important;
    }

    .msg-box { 
        padding: 20px; border-radius: 15px; margin-bottom: 20px; 
        border-right: 10px solid; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        background-color: #ffffff; line-height: 1.8;
    }
    
    .legal { border-color: #1d4ed8; background-color: #eff6ff; }
    .psych { border-color: #7c3aed; background-color: #f5f3ff; }
    .strat { border-color: #ea580c; background-color: #fffbeb; }
    
    .stButton > button { width: 100%; border-radius: 10px; font-weight: 700; height: 3.5em; background: #1e293b; color: white; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. وظائف المعالجة الذكية
# =============================================
def extract_pdf_clean(file_obj):
    try:
        file_obj.seek(0)
        pdf_data = file_obj.read()
        text = ""
        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            for page in doc: text += page.get_text() + " "
        return re.sub(r'\s+', ' ', text).strip()
    except Exception: return ""

# =============================================
# 3. إدارة الجلسة والسايدبار المنظم
# =============================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header("🛡️ مركز القيادة")
    api_key = st.text_input("Gemini API Key:", type="password")
    
    # تحديث الموديلات لعام 2026 لتجنب 404
    model_choice = st.selectbox("اختر الموديل (2026 Update):", [
        "gemini-2.0-flash", 
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro"
    ])
    
    st.divider()
    with st.expander("📂 إدارة المستندات", expanded=True):
        v_files = st.file_uploader("📂 خزنة أدلتنا", type=["pdf"], accept_multiple_files=True)
        o_files = st.file_uploader("⚔️ ملفات الخصم", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح الجلسة"):
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# عرض المحادثات السابقة
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# =============================================
# 4. محرك التنفيذ (Logic) - الإصلاح الشامل
# =============================================
with st.container():
    query = st.text_area("اشرح الموقف أو اطلب تحليلاً محددًا:", placeholder="اكتب هنا...")
    c1, c2, c3 = st.columns(3)
    btn_L = c1.button("⚖️ تحليل قانوني")
    btn_P = c2.button("🧠 تحليل نفسي")
    btn_S = c3.button("🧨 داهية استراتيجي")

if (btn_L or btn_P or btn_S) and api_key and query:
    try:
        # الإعداد الصحيح للموديل (يمنع أخطاء التسمية)
        genai.configure(api_key=api_key)
        # التأكد من عدم تكرار كلمة models/
        clean_model = model_choice.split('/')[-1]
        model = genai.GenerativeModel(model_name=f"models/{clean_model}")
        
        with st.spinner("⚔️ جاري معالجة البيانات وتوليد الاستراتيجية..."):
            # استخراج النصوص
            v_txt = " ".join([extract_pdf_clean(f) for f in v_files]) if v_files else ""
            o_txt = " ".join([extract_pdf_clean(f) for f in o_files]) if o_files else ""

            # تحديد الشخصية والبرومبت
            if btn_L:
                label, style, role = "⚖️ المحلل القانوني", "legal", "خبير قانوني متخصص في الثغرات والأنظمة"
            elif btn_P:
                label, style, role = "🧠 المحلل النفسي", "psych", "خبير في سيكولوجية التفاوض ونقاط الضعف البشرية"
            else:
                label, style, role = "🧨 الداهية الاستراتيجي", "strat", "مخطط استراتيجي داهية يبحث عن حلول خارج الصندوق"

            full_prompt = f"""
            أنت في دور: {role}.
            مستنداتنا: {v_txt[:7000]}
            مستندات الخصم: {o_txt[:7000]}
            المهمة: {query}
            
            أجب باللغة العربية، بأسلوب عرض منظم (نقاط)، ركز على الحلول العملية المباشرة.
            """
            
            # توليد المحتوى
            response = model.generate_content(full_prompt)
            
            if response.text:
                st.session_state.chat_history.append({
                    "label": label, 
                    "content": response.text, 
                    "style": style
                })
                st.rerun()

    except Exception as e:
        st.error(f"⚠️ حدث خطأ في النظام: {e}")

# =============================================
# 5. التقرير النهائي الموحد
# =============================================
if st.session_state.chat_history:
    st.divider()
    report_data = f"--- تقرير Strategic War Room ---\nالتاريخ: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    for c in st.session_state.chat_history:
        report_data += f"[{c['label']}]:\n{c['content']}\n{'-'*20}\n"

    st.download_button(
        label="📥 تحميل التقرير الرسمي الكامل",
        data=report_data.encode('utf-8'),
        file_name=f"War_Room_Report_{datetime.now().strftime('%H%M%S')}.txt",
        mime="text/plain"
    )
