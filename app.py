# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import re
from datetime import datetime

# =============================================
# 1. إعدادات الواجهة (منع تقطع الحروف وتنسيق RTL)
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
        word-break: keep-all !important; 
        line-height: 1.8 !important;
    }
    
    .msg-box { 
        padding: 25px; border-radius: 15px; margin-bottom: 20px; 
        border-right: 12px solid; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        width: 100% !important;
    }
    
    .legal { border-color: #3b82f6; background-color: #eff6ff; color: #1e3a8a; }
    .psych { border-color: #8b5cf6; background-color: #f5f3ff; color: #2e1065; }
    .strat { border-color: #f59e0b; background-color: #fffbeb; color: #451a03; }
    
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
    except Exception as e: return f"[خطأ في قراءة الملف: {e}]"

# =============================================
# 3. إدارة الجلسة والواجهة الجانبية
# =============================================
if "chat_log" not in st.session_state: 
    st.session_state.chat_log = []

with st.sidebar:
    st.header("🛡️ مركز القيادة الاستراتيجي")
    key = st.text_input("Gemini API Key:", type="password")
    
    model_choice = st.selectbox("اختر الموديل:", [
        "gemini-1.5-flash", 
        "gemini-1.5-pro", 
        "gemini-1.0-pro"
    ])
    
    st.divider()
    v_files = st.file_uploader("📂 خزنة الأدلة (Vault)", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ ملفات الخصم (Opponent)", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح الجلسة بالكامل"): 
        st.session_state.chat_log = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# عرض المحادثات السابقة
for chat in st.session_state.chat_log:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# منطقة الإدخال والتحليل
with st.form("main_form", clear_on_submit=True):
    query = st.text_area("اشرح الموقف أو اطلب تحليلاً محددًا:")
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ تحليل قانوني")
    with c2: btn_P = st.form_submit_button("🧠 تحليل نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية استراتيجي")

# =============================================
# 4. محرك التنفيذ (Logic)
# =============================================
if (btn_L or btn_P or btn_S) and key and query:
    try:
        genai.configure(api_key=key)
        
        # الحل الجذري لخطأ 404: تنظيف اسم الموديل وتنسيقه
        clean_model_name = model_choice.replace("models/", "")
        model = genai.GenerativeModel(model_name=f"models/{clean_model_name}")
        
        # استخراج النصوص من الملفات المرفوعة
        v_txt = "".join([extract_pdf(f) for f in v_files]) if v_files else "لا توجد مستندات لنا."
        o_txt = "".join([extract_pdf(f) for f in o_files]) if o_files else "لا توجد مستندات للخصم."

        # تحديد الشخصية بناءً على الزر
        if btn_L:
            label, style, role = "⚖️ المحلل القانوني", "legal", "خبير قانوني متخصص في الثغرات والأنظمة"
        elif btn_P:
            label, style, role = "🧠 المحلل النفسي", "psych", "خبير في سيكولوجية التفاوض ونقاط الضعف البشرية"
        else:
            label, style, role = "🧨 الداهية الاستراتيجي", "strat", "مخطط استراتيجي لا يرحم يبحث عن حلول خارج الصندوق"

        # بناء البرومبت الاحترافي
        prompt = f"""
        أنت الآن في دور: {role}.
        سياق مستنداتنا: {v_txt[:10000]}
        سياق مستندات الخصم: {o_txt[:10000]}
        المهمة المطلوبة: {query}
        
        أجب باللغة العربية، بأسلوب عرض منظم (نقاط)، ركز على الحلول العملية والثغرات المتاحة.
        """
        
        with st.spinner("⚔️ جاري معالجة البيانات وتوليد الاستراتيجية..."):
            res = model.generate_content(prompt)
            if res.text:
                st.session_state.chat_log.append({"label": label, "content": res.text, "style": style})
                st.rerun()
            else:
                st.warning("⚠️ حجب الموديل الاستجابة لأسباب تتعلق بالأمان.")
                
    except Exception as e:
        st.error(f"⚠️ حدث خطأ: {e}")

# =============================================
# 5. التقرير الاستراتيجي الموحد
# =============================================
if st.session_state.chat_log:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    
    report_content = f"--- تقرير Strategic War Room ---\nالتاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    for c in st.session_state.chat_log:
        report_content += f"[{c['label']}]:\n{c['content']}\n{'-'*30}\n"

    st.download_button(
        label="📥 تحميل التقرير الرسمي الكامل",
        data=report_content.encode('utf-8'),
        file_name=f"War_Room_Report_{datetime.now().strftime('%H%M%S')}.txt",
        mime="text/plain"
    )
