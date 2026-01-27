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

    /* حل مشكلة النص العمودي: فرض الانسياب الأفقي الواسع */
    .stMarkdown, p, div, [data-testid="stMarkdownContainer"] {
        direction: rtl !important;
        text-align: right !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        display: block !important;
    }

    .msg-box { 
        padding: 25px; border-radius: 15px; margin-bottom: 20px; 
        border-right: 10px solid; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        background-color: #ffffff; line-height: 1.8;
    }
    
    .legal { border-color: #1d4ed8; background-color: #eff6ff; }
    .psych { border-color: #7c3aed; background-color: #f5f3ff; }
    .strat { border-color: #ea580c; background-color: #fffbeb; }
    
    .stButton > button { 
        width: 100%; border-radius: 10px; font-weight: 700; 
        height: 3.5em; background: #1e293b; color: white; 
    }
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
# 3. إدارة الجلسة والسايدبار
# =============================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header("🛡️ مركز القيادة الاستراتيجي")
    api_key = st.text_input("Gemini API Key:", type="password")
    
    # قائمة الموديلات المحدثة لعام 2026
    model_choice = st.selectbox("اختر الموديل:", [
        "gemini-2.0-flash", 
        "gemini-1.5-pro",
        "gemini-1.5-flash"
    ])
    
    st.divider()
    with st.expander("📂 إدارة المستندات", expanded=True):
        v_files = st.file_uploader("📂 ملفاتنا (Vault)", type=["pdf"], accept_multiple_files=True)
        o_files = st.file_uploader("⚔️ ملفات الخصم (Opponent)", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح الجلسة بالكامل"):
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# عرض سجل المحادثات
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# =============================================
# 4. منطقة التنفيذ (Logic)
# =============================================
with st.container():
    query = st.text_area("اشرح الموقف أو اطلب تحليلاً محددًا:", placeholder="اكتب تفاصيل القضية أو المهمة هنا...")
    c1, c2, c3 = st.columns(3)
    
    # الأزرار تعمل بشكل مستقل لمنع تعليق الصفحة
    btn_L = c1.button("⚖️ تحليل قانوني")
    btn_P = c2.button("🧠 تحليل نفسي")
    btn_S = c3.button("🧨 داهية استراتيجي")

if (btn_L or btn_P or btn_S) and api_key and query:
    try:
        genai.configure(api_key=api_key)
        # تصحيح مسار الموديل لضمان التوافق مع SDK
        model_name_fixed = model_choice.replace("models/", "")
        model = genai.GenerativeModel(model_name=f"models/{model_name_fixed}")
        
        with st.spinner("⚔️ جاري تحليل البيانات وبناء الاستراتيجية..."):
            # استخراج محتوى الملفات
            v_txt = " ".join([extract_pdf_clean(f) for f in v_files])
            o_txt = " ".join([extract_pdf_clean(f) for f in o_files])

            # تخصيص الدور والأسلوب
            if btn_L:
                label, style, role = "⚖️ المحلل القانوني", "legal", "خبير قانوني متخصص في الثغرات"
            elif btn_P:
                label, style, role = "🧠 المحلل النفسي", "psych", "خبير في سيكولوجية التفاوض"
            else:
                label, style, role = "🧨 الداهية الاستراتيجي", "strat", "مخطط استراتيجي لا يرحم"

            prompt = f"""
            دورك الآن: {role}.
            سياق ملفاتنا: {v_txt[:8000]}
            سياق ملفات الخصم: {o_txt[:8000]}
            السؤال/المهمة: {query}
            
            أجب باللغة العربية، بأسلوب نقاط واضحة، ركز على الحلول العملية المباشرة.
            """
            
            response = model.generate_content(prompt)
            
            if response.text:
                st.session_state.chat_history.append({
                    "label": label, 
                    "content": response.text, 
                    "style": style
                })
                st.rerun()

    except Exception as e:
        st.error(f"⚠️ خطأ فني: {e}")

# =============================================
# 5. تصدير التقارير الرسمية
# =============================================
if st.session_state.chat_history:
    st.divider()
    report_text = f"--- تقرير غرفة العمليات الاستراتيجية ---\nالتاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    for c in st.session_state.chat_history:
        report_text += f"[{c['label']}]:\n{c['content']}\n{'-'*30}\n"

    st.download_button(
        label="📥 تحميل التقرير النهائي (TXT)",
        data=report_text.encode('utf-8'),
        file_name=f"Strategic_Report_{datetime.now().strftime('%H%M%S')}.txt",
        mime="text/plain"
    )
