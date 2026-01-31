# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
from datetime import datetime

# =============================================
# 1. PAGE SETUP & STYLING
# =============================================
st.set_page_config(page_title="The Classico", layout="centered")

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important; 
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    .msg-box { 
        padding: 15px; border-radius: 10px; margin-bottom: 10px; 
        border-right: 6px solid; background-color: #ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        width: 100%;
        word-wrap: break-word;
    }
    .legal { border-color: #1d4ed8; background-color: #eff6ff; color: #1e3a8a; }
    .strat { border-color: #ea580c; background-color: #fffbeb; color: #451a03; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. CONSTITUTION & SESSION STATE
# =============================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

CONSTITUTION = """
1. Reverse Engineering: Write the ending first.
2. The Triple Strike: Legal, Financial, Psychological.
3. Controlled Alternatives: Choice architecture.
4. Information Embargo: No burning cards early.
5. Identify 'The Mother': Target the root cause.
6. Poker Face: Zero unintended words.
7. Shadow Tracking: Flag conspiracy links.
"""

# =============================================
# 3. INTERFACE
# =============================================
st.title("⚖️ The Classico Boardroom")

api_key = st.secrets.get("GEMINI_API_KEY", None)

if st.button("🗑️ مسح الذاكرة"):
    st.session_state.chat_history = []
    st.rerun()

query = st.text_area("اشرح الموقف الاستراتيجي:", height=150)

# =============================================
# 4. THE CLASSICO ENGINE
# =============================================
def run_classico(user_query):
    try:
        genai.configure(api_key=api_key)
        
        # FIXED: Explicit model path to prevent 404
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        with st.spinner("⚔️ جاري استدعاء الشركات والتدقيق..."):
            full_prompt = f"""
            أنت نظام 'The Classico'. التزم بالدستور: {CONSTITUTION}
            حلل الموقف من منظور قانوني، استراتيجي، ونفسي. 
            الموقف: {user_query}
            
            يجب تقسيم الرد بدقة إلى:
            ZONE_A: (الملف القانوني الرسمي)
            ZONE_B: (خزنة الاستراتيجية السرية)
            """
            res = model.generate_content(full_prompt)

        if res and res.text:
            st.session_state.chat_history.append({"content": res.text})
            st.rerun()
    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")

if st.button("🚀 إطلاق العملية", use_container_width=True):
    if query and api_key:
        run_classico(query)
    elif not api_key:
        st.error("⚠️ API Key Missing in Secrets")

# =============================================
# 5. OUTPUT DISPLAY
# =============================================
if st.session_state.chat_history:
    latest = st.session_state.chat_history[-1]["content"]
    st.divider()
    
    if "ZONE_A" in latest and "ZONE_B" in latest:
        # Splitting logic
        parts = latest.split("ZONE_B:")
        z_a = parts[0].replace("ZONE_A:", "").strip()
        z_b = parts[1].strip()
        
        t1, t2 = st.tabs(["📄 Zone A (قانوني)", "🔐 Zone B (استراتيجي)"])
        with t1:
            st.markdown(f'<div class="msg-box legal">{z_a}</div>', unsafe_allow_html=True)
        with t2:
            st.markdown(f'<div class="msg-box strat">{z_b}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="msg-box">{latest}</div>', unsafe_allow_html=True)
