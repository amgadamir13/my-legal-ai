import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io

# --- 1. هندسة الواجهة (تنسيق الحماية من الحروف المقطعة) ---
st.set_page_config(page_title="المستشار الاستراتيجي Pro", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* منع الحروف العمودية نهائياً وضمان تدفق النص العربي */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] p {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: pre-wrap !important;
        word-break: keep-all !important;
        overflow-wrap: break-word !important;
    }

    /* تنسيق فقاعات المحادثة لضمان التمدد الأفقي */
    .msg-box { 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        line-height: 1.8; 
        border-right: 8px solid;
        min-width: 280px;
        max-width: 100%;
        width: auto;
        display: block;
    }
    
    .user-style { background-color: #1e293b; border-color: #3b82f6; color: #f8fafc; }
    .legal-style { background-color: #064e3b; border-color: #10b981; color: #ecfdf5; }
    .psych-style { background-color: #4c1d95; border-color: #a855f7; color: #f5f3ff; }
    .street-style { background-color: #7f1d1d; border-color: #f43f5e; color: #fff1f2; }

    .stTextArea textarea { direction: rtl !important; text-align: right !important; }
    input[type="password"] { direction: ltr !important; text-align: left !important; }
    .stButton button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background-color: #1e3a8a; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. القائمة الجانبية (Command Center) ---
with st.sidebar:
    st.header("🛡️ الخزنة الاستراتيجية")
    api_key = st.text_input("مفتاح Gemini:", type="password")
    
    st.divider()
    strategy_input = st.text_input("ميثاقنا (مثلاً: الصبر، الحزم):", "الحكمة")
    
    st.divider()
    my_docs = st.file_uploader("📂 حقائبي (الخزنة)", accept_multiple_files=True)
    opp_docs = st.file_uploader("🚩 ملفات الخصم", accept_multiple_files=True)
    
    if st.button("مسح السجل 🗑️"):
        st.session_state.messages = []
        st.rerun()

# --- 4. واجهة المحادثة ---
st.title("⚖️ المحقق الاستراتيجي")

for m in st.session_state.messages:
    style = m.get("style", "user-style")
    label = m.get("label", "👤 أنت")
    st.markdown(f'<div class="msg-box {style}"><b>{label}:</b><br>{m["content"]}</div>', unsafe_allow_html=True)

# --- 5. محرك العقول الثلاثة ---
with st.form("action_form", clear_on_submit=True):
    user_input = st.text_area("اشرح الموقف أو التطور الجديد...", height=100)
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

if (btn_L or btn_P or btn_S) and api_key and user_input:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # اختيار الشخصية
        if btn_L: role, label, style = "محامي جنائي يستخرج الثغرات", "⚖️ القانوني", "legal-style"
        elif btn_P: role, label, style = "محلل نفسي يكتشف الكذب والغرور", "🧠 النفسي", "psych-style"
        else: role, label, style = "داهية شوارع يجد حلولاً غير تقليدية", "🧨 الداهية", "street-style"

        # استخراج نصوص الملفات (Vault & Opponent)
        v_txt = "".join([fitz.open(stream=f.read(), filetype="pdf").get_page_text(0) for f in my_docs if f.type=="application/pdf"])
        o_txt = "".join([fitz.open(stream=f.read(), filetype="pdf").get_page_text(0) for f in opp_docs if f.type=="application/pdf"])

        prompt = f"""
        دورك: {role}. استراتيجيتنا: {strategy_input}.
        تاريخنا المشترك المكتوب في الخزنة: {v_txt[:7000]}
        ما يدعيه الخصم الآن: {o_txt[:7000]}
        سؤال المستخدم: {user_input}
        
        أجب بدقة وبالعربية الفصحى المنظمة جداً.
        """
        
        with st.spinner("جاري التفكير الاستراتيجي..."):
            response = model.generate_content(prompt)
            st.session_state.messages.append({"role": "user", "content": user_input, "label": "👤 أنت", "style": "user-style"})
            st.session_state.messages.append({"role": "assistant", "content": response.text, "label": label, "style": style})
            st.rerun()
            
    except Exception as e:
        st.error(f"خطأ: {e}")
