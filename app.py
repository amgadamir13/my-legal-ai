# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions as gapi_errors
from datetime import datetime

# =============================================
# 1. PAGE SETUP & STYLING (YOUR ORIGINAL CRITERIA)
# =============================================
st.set_page_config(page_title="Strategic War Room Pro", layout="centered")

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
# 2. SESSION STATE & CONSTITUTION
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
# 3. MAIN APP INTERFACE
# =============================================
st.title("⚖️ Strategic War Room Pro")

api_key = st.secrets.get("GEMINI_API_KEY", None)

model_choice = st.selectbox("اختر الموديل:", [
    "gemini-1.5-flash",
    "gemini-1.5-pro"
])

if st.button("🗑️ مسح الذاكرة"):
    st.session_state.chat_history = []
    st.rerun()

query = st.text_area("اشرح الموقف الاستراتيجي:", height=120)

# =============================================
# 4. PROCESSING LOGIC (THE CLASSICO FLOW)
# =============================================
def run_classico_analysis(user_query):
    try:
        genai.configure(api_key=api_key)
        # Using the v1beta endpoint implicitly via the library
        model = genai.GenerativeModel(model_choice)
        
        with st.spinner("⚔️ جاري استدعاء الشركات والتدقيق..."):
            full_prompt = f"""
            أنت نظام 'The Classico'. التزم بالدستور: {CONSTITUTION}
            المهمة: قم بتحليل الموقف من منظور قانوني، استراتيجي، ونفسي. 
            الموقف: {user_query}
            
            المخرجات المطلوبة حصراً بهذا التنسيق:
            ZONE_A: (الملف القانوني) - اكتب هنا.
            ZONE_B: (الخزنة السرية) - اكتب هنا.
            """
            res = model.generate_content(full_prompt)

        if res and res.text:
            st.session_state.chat_history.append({"content": res.text})
            st.rerun()
    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")

if st.button("🚀 إطلاق عملية الكلاسيكو", use_container_width=True):
    if query and api_key:
        run_classico_analysis(query)
    elif not api_key:
        st.error("⚠️ مفتاح API مفقود!")

# =============================================
# 5. DUAL-ZONE DISPLAY
# =============================================
if st.session_state.chat_history:
    latest = st.session_state.chat_history[-1]["content"]
    
    st.divider()
    
    # Logic to split the zones for the UI
    if "ZONE_A:" in latest and "ZONE_B:" in latest:
        parts = latest.split("ZONE_B:")
        zone_a = parts[0].replace("ZONE_A:", "").strip()
        zone_b = parts[1].strip()
        
        tab1, tab2 = st.tabs(["📄 Zone A (قانوني)", "🔐 Zone B (استراتيجي)"])
        
        with tab1:
            st.markdown(f'<div class="msg-box legal"><b>🏛️ التقرير الرسمي:</b><br>{zone_a}</div>', unsafe_allow_html=True)
            st.download_button("📥 تحميل للمحامي", zone_a)
            
        with tab2:
            st.markdown(f'<div class="msg-box strat"><b>🧨 الخزنة السرية:</b><br>{zone_b}</div>', unsafe_allow_html=True)
    else:
        # Fallback if the AI doesn't follow the ZONE format perfectly
        st.markdown(f'<div class="msg-box">{latest}</div>', unsafe_allow_html=True)
