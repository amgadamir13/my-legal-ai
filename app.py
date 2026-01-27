import streamlit as st
import google.generativeai as genai
import os
import fitz  # PyMuPDF
from PIL import Image

# --- 1. إعداد هيكل المجلدات ---
if not os.path.exists("documents"):
    os.makedirs("documents")

# --- 2. هندسة الواجهة الفاخرة (حل مشكلة الحروف للأيفون) ---
st.set_page_config(page_title="المستشار الاستراتيجي Pro", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* منع تقطع الحروف العربية نهائياً */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] p {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: pre-wrap !important;
        word-break: keep-all !important;
    }

    .msg-box { 
        padding: 20px; border-radius: 18px; margin-bottom: 15px; line-height: 1.8; 
        border-right: 10px solid; display: block !important; unicode-bidi: isolate !important;
    }
    
    .user-style { background-color: #1e293b; border-color: #3b82f6; color: #f8fafc; }
    .legal-style { background-color: #064e3b; border-color: #10b981; color: #ecfdf5; }
    .psych-style { background-color: #2e1065; border-color: #a855f7; color: #f5f3ff; }
    .street-style { background-color: #450a0a; border-color: #ef4444; color: #fff1f2; }

    /* تنسيق المدخلات */
    .stTextArea textarea { direction: rtl !important; text-align: right !important; background-color: #1e293b !important; color: white !important; }
    input[type="password"] { direction: ltr !important; text-align: left !important; }
    .stButton button { width: 100%; border-radius: 12px; height: 3.5em; background: linear-gradient(90deg, #1e3a8a, #1d4ed8); color: white; font-weight: bold; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. إدارة الذاكرة ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 4. القائمة الجانبية (مركز القيادة) ---
with st.sidebar:
    st.title("🛡️ الخزنة الاستراتيجية")
    api_key = st.text_input("Gemini API Key:", type="password")
    st.divider()
    strategy_val = st.text_input("ميثاقنا (القيم):", "الحكمة والانتصار")
    st.divider()
    my_vault = st.file_uploader("📂 حقائبي (الخزنة):", accept_multiple_files=True, key="v")
    opp_docs = st.file_uploader("🚩 أوراق الخصم:", accept_multiple_files=True, key="o")
    if st.button("تفريغ الجلسة 🗑️"):
        st.session_state.chat_history = []
        st.rerun()

# --- 5. واجهة العرض ---
st.title("⚖️ المحقق الاستراتيجي Pro")

for chat in st.session_state.chat_history:
    style = chat.get("style", "user-style")
    label = chat.get("label", "👤 أنت")
    st.markdown(f'<div class="msg-box {style}"><b>{label}:</b><br>{chat["content"]}</div>', unsafe_allow_html=True)

# --- 6. المحرك الثلاثي ---
with st.form("strategic_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف أو ارفع رسالة الخصم هنا:", height=100)
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

if (btn_L or btn_P or btn_S) and api_key and user_query:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # تحديد الشخصية واللون
        if btn_L: role, label, style = "محامي خبير بالثغرات", "⚖️ القانوني", "legal-style"
        elif btn_P: role, label, style = "محلل نفسي جنائي خبير", "🧠 النفسي", "psych-style"
        else: role, label, style = "مفاوض شوارع داهية", "🧨 الداهية", "street-style"

        # قراءة الملفات
        def process_docs(files):
            text = ""
            for f in files:
                if f.type == "application/pdf":
                    with fitz.open(stream=f.read(), filetype="pdf") as doc:
                        text += "".join([p.get_text() for p in doc])
            return text

        v_context = process_docs(my_vault)
        o_context = process_docs(opp_docs)

        # البرومبت العبقري
        prompt = f"""
        أنت الآن بصفة: {role}. قيمنا: {strategy_val}.
        خلفية تاريخية (الخزنة): {v_context[:8000]}
        ادعاءات الخصم: {o_context[:8000]}
        الموقف الحالي: {user_query}
        
        حلل واكشف الثغرات والتناقضات بأسلوب منظم جداً وباللغة العربية الفصحى.
        """
        
        with st.spinner("جاري التحليل..."):
            response = model.generate_content(prompt)
            st.session_state.chat_history.append({"role": "user", "content": user_query, "label": "👤 أنت", "style": "user-style"})
            st.session_state.chat_history.append({"role": "assistant", "content": response.text, "label": label, "style": style})
            st.rerun()
    except Exception as e:
        st.error(f"خطأ: {e}")
