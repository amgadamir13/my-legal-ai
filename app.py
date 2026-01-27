# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions as gapi_errors
import fitz  # PyMuPDF
import re

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
    
    /* فرض الانسياب الأفقي ومنع تقطع الكلمات */
    p, div, span, [data-testid="stMarkdownContainer"] p {
        white-space: normal !important;
        word-wrap: break-word !important;
        line-height: 1.8 !important;
        text-align: right !important;
    }
    
    .msg-box { 
        padding: 25px; border-radius: 15px; margin-bottom: 20px; 
        border-right: 12px solid; background-color: #ffffff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        width: 100%;
    }
    
    .legal { border-color: #1d4ed8; background-color: #eff6ff; color: #1e3a8a; }
    .psych { border-color: #7c3aed; background-color: #f5f3ff; color: #2e1065; }
    .strat { border-color: #ea580c; background-color: #fffbeb; color: #451a03; }
    
    /* تحسين شكل الأزرار */
    .stButton > button { width: 100%; font-weight: 700; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. وظائف المعالجة
# =============================================
def extract_pdf_clean(file_obj):
    try:
        file_obj.seek(0)
        pdf_data = file_obj.read()
        text = ""
        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            for page in doc: text += page.get_text() + " "
        return re.sub(r'\s+', ' ', text).strip()
    except: return ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =============================================
# 3. الشريط الجانبي (Sidebar)
# =============================================
with st.sidebar:
    st.header("🛡️ مركز القيادة الاستراتيجي")
    api_key = st.text_input("Gemini API Key:", type="password", help="أدخل المفتاح واضغط Enter")
    
    model_choice = st.selectbox("اختر الموديل:", [
        "gemini-2.0-flash-exp", 
        "gemini-1.5-pro", 
        "gemini-1.5-flash"
    ])
    
    max_chars = st.slider("🔧 قوة المسح (عدد الحروف):", 1000, 15000, 5000)
    st.divider()
    
    st.subheader("📂 رفع المستندات")
    v_files = st.file_uploader("خزنة مستنداتنا", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("مستندات الخصم", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح ذاكرة الجلسة"):
        st.session_state.chat_history = []
        st.rerun()

# =============================================
# 4. المحرك الرئيسي
# =============================================
st.title("⚖️ Strategic War Room Pro")

# عرض سجل المحادثة بتنسيق منظم
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

with st.form("main_analysis_form", clear_on_submit=True):
    query = st.text_area("اشرح الموقف المطلوب تحليله بعمق:")
    c1, c2, c3 = st.columns(3)
    btn_L = c1.form_submit_button("⚖️ تحليل قانوني")
    btn_P = c2.form_submit_button("🧠 تحليل نفسي")
    btn_S = c3.form_submit_button("🧨 داهية استراتيجي")

if (btn_L or btn_P or btn_S):
    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح API في القائمة الجانبية أولاً.")
    elif not query:
        st.warning("⚠️ يرجى شرح الموقف قبل بدء التحليل.")
    else:
        try:
            genai.configure(api_key=api_key)
            full_model_name = f"models/{model_choice}" if "models/" not in model_choice else model_choice
            
            # إعدادات الأمان
            safe = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
            
            model = genai.GenerativeModel(model_name=full_model_name, safety_settings=safe)
            
            with st.spinner("⚔️ جاري استحضار العقول الاستراتيجية وفحص المستندات..."):
                v_txt = " ".join([extract_pdf_clean(f) for f in v_files])
                o_txt = " ".join([extract_pdf_clean(f) for f in o_files])

                if btn_L: label, style, role = "⚖️ المحلل القانوني", "legal", "خبير قانوني متخصص في الثغرات"
                elif btn_P: label, style, role = "🧠 المحلل النفسي", "psych", "خبير سيكولوجيا الصراعات والتفاوض"
                else: label, style, role = "🧨 الداهية الاستراتيجي", "strat", "مخطط استراتيجي داهية لا يرحم"

                # بناء البرومبت بأسلوب منظم
                prompt = f"""
                بصفتك {role}.
                سياق مستنداتنا: {v_txt[:max_chars]}
                سياق مستندات الخصم: {o_txt[:max_chars]}
                الموقف الحالي: {query}
                
                المطلوب: تحليل استراتيجي دقيق، منظم في نقاط، يقدم حلولاً عملية وثغرات يمكن استغلالها. أجب باللغة العربية.
                """
                
                response = model.generate_content(prompt)
                if response.text:
                    st.session_state.chat_history.append({"label": label, "content": response.text, "style": style})
                    st.rerun()

        except gapi_errors.ResourceExhausted:
            st.error("⚠️ انتهت حصة الاستخدام (Quota). يرجى الانتظار دقيقة أو تغيير الموديل.")
        except Exception as e:
            st.error(f"⚠️ حدث خطأ فني: {e}")
