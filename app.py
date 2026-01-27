import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io

# --- 1. إصلاح الهيكل البصري (The Nuclear Fix for Arabic Layout) ---
st.set_page_config(page_title="Strategic War Room", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* منع الحروف العمودية وتثبيت الاتجاه */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: normal !important; /* يمنع الحروف من النزول عمودياً */
        word-wrap: break-word !important;
    }

    /* إصلاح فقاعات الكلام لمنع التداخل جهة اليسار */
    .msg-box { 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        line-height: 1.6; 
        border-right: 8px solid;
        max-width: 100%;
        display: block; /* يضمن بقاء النص أفقياً */
    }
    .user-style { background-color: #1e293b; border-color: #3b82f6; color: #f8fafc; }
    .legal-style { background-color: #064e3b; border-color: #10b981; color: #ecfdf5; }
    .psych-style { background-color: #4c1d95; border-color: #a855f7; color: #f5f3ff; }
    .street-style { background-color: #7f1d1d; border-color: #f43f5e; color: #fff1f2; }
    .opponent-style { background-color: #334155; border-color: #94a3b8; color: #cbd5e1; } /* لون الخصم */

    input[type="password"] { direction: ltr !important; text-align: left !important; }
    .stButton button { border-radius: 12px; font-weight: bold; width: 100%; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الذاكرة ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 3. مركز القيادة ---
with st.sidebar:
    st.header("🛡️ مركز القيادة")
    api_key = st.text_input("مفتاح Gemini:", type="password")
    v_files = st.file_uploader("قبو حقائقي", accept_multiple_files=True)
    o_files = st.file_uploader("ملفات الخصم", accept_multiple_files=True)
    if st.button("تصفير الذاكرة 🗑️"):
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ المحقق الاستراتيجي")

# --- 4. عرض المحادثة (Fixed Alignment) ---
for chat in st.session_state.chat_history:
    style = chat.get("style", "user-style")
    label = chat.get("label", "👤 أنت")
    st.markdown(f'<div class="msg-box {style}"><b>{label}:</b><br>{chat["content"]}</div>', unsafe_allow_html=True)

# --- 5. محرك العقول الأربعة (إضافة محاكي الخصم) ---
with st.form("war_room_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف الحالي...", height=100)
    c1, c2, c3, c4 = st.columns(4)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")
    with c4: btn_O = st.form_submit_button("👺 الخصم") # ميزة المحاكاة

if (btn_L or btn_P or btn_S or btn_O) and api_key and user_query:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # اختيار الهوية
        if btn_L: role, label, style = "مستشار قانوني خبير", "⚖️ القانوني", "legal-style"
        elif btn_P: role, label, style = "محلل نفسي جنائي", "🧠 النفسي", "psych-style"
        elif btn_S: role, label, style = "مفاوض داهية", "🧨 الداهية", "street-style"
        else: role, label, style = "تقمص شخصية خصمي اللدود وحاول الرد على حججي لإيجاد ثغراتي", "👺 محاكي الخصم", "opponent-style"

        # قراءة الملفات
        v_context = ""
        for f in (v_files if v_files else []):
            if f.type == "application/pdf":
                with fitz.open(stream=f.read(), filetype="pdf") as doc:
                    for page in doc: v_context += page.get_text() + "\n"

        prompt = f"دورك: {role}. السياق: {v_context[:8000]}. السؤال: {user_query}"
        
        with st.spinner(f"جاري استحضار {label}..."):
            response = model.generate_content(prompt)
            st.session_state.chat_history.append({"role": "user", "content": user_query, "label": "👤 أنت", "style": "user-style"})
            st.session_state.chat_history.append({"role": "assistant", "content": response.text, "label": label, "style": style})
            st.rerun()
    except Exception as e:
        st.error(f"خطأ: {e}")
