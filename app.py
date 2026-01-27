import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import io
import traceback
import re
from typing import List

# 1. إعداد الصفحة ومنع الانهيار العمودي للنص
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] p {
        direction: rtl !important; text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: pre-wrap !important;
        word-break: keep-all !important; /* يمنع ظهور الحروف عمودياً */
    }
    .msg-box { 
        padding: 20px; border-radius: 15px; margin-bottom: 20px; 
        line-height: 1.8; border-right: 12px solid; 
        box-shadow: 0 5px 15px rgba(0,0,0,0.08); width: 100% !important;
    }
    .user-style { border-color: #1e3a8a; background-color: #f8fafc; color: #1e3a8a; }
    .ai-style { border-color: #10b981; background-color: #f0fdf4; color: #14532d; }
    .finding-card {
        background: #ffffff; padding: 25px; border-radius: 15px;
        margin-bottom: 20px; border-right: 8px solid #cbd5e1; width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. تعريف الدوال الأساسية قبل استخدامها
def normalize_arabic_text(text: str) -> str:
    if not text: return ""
    text = text.replace("\u200c", "").replace("\u200d", "")
    text = re.sub(r'(?<=[\u0600-\u06FF])\s*\n\s*(?=[\u0600-\u06FF])', '', text)
    return text.strip()

def get_text_from_files(files) -> str:
    text = ""
    if not files: return ""
    for f in files:
        try:
            with fitz.open(stream=f.read(), filetype="pdf") as doc:
                for page in doc: text += page.get_text() + "\n"
        except: continue
    return normalize_arabic_text(text)

# 3. إعداد حالة الجلسة
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 4. الشريط الجانبي (تعريف المتغيرات أولاً)
with st.sidebar:
    st.title("🛡️ مركز القيادة")
    api_key = st.text_input("مفتاح Gemini السري:", type="password")
    model_name = st.selectbox("النموذج:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    st.divider()
    v_files = st.file_uploader("قبو الحقائق (Vault):", accept_multiple_files=True)
    o_files = st.file_uploader("ملفات الخصم (Opponent):", accept_multiple_files=True)
    if st.button("تفريغ الذاكرة 🗑️"):
        st.session_state.chat_history = []
        st.rerun()

# 5. الواجهة الرئيسية والنموذج
st.title("⚖️ Strategic War Room Pro")

with st.form("war_room_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف الحالي هنا:", height=100)
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

# 6. منطق التشغيل (Execution Logic)
if (btn_L or btn_P or btn_S) and user_query:
    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح الـ API في الشريط الجانبي.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            
            # تحديد الهوية
            label = "⚖️ القانوني" if btn_L else ("🧠 النفسي" if btn_P else "🧨 الداهية")
            style = "ai-style"
            
            # جمع السياق
            v_context = get_text_from_files(v_files)
            o_context = get_text_from_files(o_files)
            
            prompt = f"حلل بدقة بالعربية: حقائقي: {v_context[:5000]}. ادعاءات الخصم: {o_context[:5000]}. السؤال: {user_query}"
            
            with st.spinner("جاري استحضار الاستراتيجية..."):
                response = model.generate_content(prompt)
                st.session_state.chat_history.append({"q": user_query, "a": response.text, "label": label, "style": style})
                st.rerun()
        except Exception as e:
            st.error(f"خطأ تقني: {str(e)}")

# 7. عرض المحادثة
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box user-style"><b>👤 أنت:</b><br>{chat["q"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}:</b><br>{chat["a"]}</div>', unsafe_allow_html=True)

# 8. قسم النتائج الرسمية
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    st.markdown('<div class="finding-card"><b>🎯 التوصية:</b> راجع التحليل أعلاه لاستخراج الثغرات المباشرة.</div>', unsafe_allow_html=True)
