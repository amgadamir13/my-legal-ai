# -*- coding: utf-8 -*-
# =============================================
# 1. الاستيرادات والإعدادات الأساسية (يجب أن تكون في البداية)
# =============================================
import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions as gapi_errors
import fitz  # PyMuPDF
import re
from datetime import datetime

# هذا يجب أن يكون أول استدعاء لـ streamlit في السكريبت
st.set_page_config(page_title="Strategic War Room Pro 2026", layout="wide")

# =============================================
# 2. تخصيص CSS والتصميم
# =============================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important; 
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    
    p, div, span, [data-testid="stMarkdownContainer"] p {
        white-space: pre-wrap !important;
        word-break: keep-all !important;
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
    
    .stButton > button { width: 100%; font-weight: 700; height: 3.5em; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 3. تعريف الدوال المساعدة
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

# =============================================
# 4. تهيئة حالة الجلسة
# =============================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =============================================
# 5. الشريط الجانبي (Sidebar) - الآن يمكن استخدام with st.sidebar:
# =============================================
with st.sidebar:
    st.header("🛡️ مركز القيادة")
    api_key = st.text_input("Gemini API Key:", type="password", help="أدخل المفتاح واضغط Enter")
    
    model_choice = st.selectbox("الموديل:", [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite", 
        "gemini-2.0-flash",
        "gemini-1.5-pro"
    ])
    max_chars = st.slider("🔧 قوة المسح:", 1000, 15000, 5000)
    
    st.divider()
    v_files = st.file_uploader("📂 ملفاتنا (Vault)", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ ملفات الخصم (Opponent)", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح الذاكرة"):
        st.session_state.chat_history = []
        st.rerun()

# =============================================
# 6. المحتوى الرئيسي للتطبيق
# =============================================
st.title("⚖️ Strategic War Room Pro")

# عرض سجل الحوار
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

with st.form("strategic_form", clear_on_submit=True):
    query = st.text_area("اشرح الموقف الاستراتيجي:")
    c1, c2, c3 = st.columns(3)
    btn_L = c1.form_submit_button("⚖️ قانوني")
    btn_P = c2.form_submit_button("🧠 نفسي")
    btn_S = c3.form_submit_button("🧨 استراتيجي")

if (btn_L or btn_P or btn_S):
    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح API أولاً.")
    elif not query:
        st.warning("⚠️ يرجى كتابة السؤال أو الموقف.")
    else:
        try:
            # استخدام الطريقة الحديثة لـ Gemini API
            client = genai.Client(api_key=api_key)
            
            with st.spinner("⚔️ جاري التحليل..."):
                v_txt = " ".join([extract_pdf_clean(f) for f in v_files])
                o_txt = " ".join([extract_pdf_clean(f) for f in o_files])

                if btn_L:
                    label, style, role = ("⚖️ القانوني", "legal", "خبير قانوني متخصص في الثغرات")
                elif btn_P:
                    label, style, role = ("🧠 النفسي", "psych", "محلل نفسي وخبير تفاوض")
                else:
                    label, style, role = ("🧨 الاستراتيجي", "strat", "مخطط استراتيجي داهية")

                prompt = f"أنت {role}. مستنداتنا: {v_txt[:max_chars]}. الخصم: {o_txt[:max_chars]}. الموقف: {query}. أجب بالعربية بنقاط."
                
                res = client.models.generate_content(
                    model=model_choice,
                    contents=prompt
                )
                
                if res.text:
                    st.session_state.chat_history.append({"label": label, "content": res.text, "style": style})
                    st.rerun()

        except gapi_errors.ResourceExhausted:
            st.error("""
            ⚠️ **انتهت الحصة المجانية لهذا الموديل.**
            *جرب تبديل الموديل في الشريط الجانبي إلى **'gemini-2.5-flash'** (الخيار الأول).*
            """)
        except Exception as e:
            st.error(f"⚠️ خطأ: {e}")

# =============================================
# 7. قسم التقرير الرسمي
# =============================================
if st.session_state.chat_history:
    st.divider()
    st.markdown('<div id="official-findings"></div>', unsafe_allow_html=True)
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    
    full_report = f"--- تقرير Strategic War Room ---\nالتاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    for c in st.session_state.chat_history:
        full_report += f"[{c['label']}]:\n{c['content']}\n{'-'*30}\n"

    st.download_button(
        label="📥 تحميل التقرير الرسمي الكامل",
        data=full_report.encode('utf-8'),
        file_name=f"Strategic_Report_{datetime.now().strftime('%y%m%d')}.txt",
        mime="text/plain"
    )
