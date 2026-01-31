# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions as gapi_errors
from datetime import datetime

# =============================================
# 1. PAGE SETUP & STYLING
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
    }
    .legal { border-color: #1d4ed8; background-color: #eff6ff; color: #1e3a8a; }
    .vault { border-color: #dc2626; background-color: #fef2f2; color: #7f1d1d; border-style: dashed; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. SESSION STATE
# =============================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =============================================
# 3. MAIN APP INTERFACE
# =============================================
st.title("⚖️ Strategic War Room Pro")

api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    st.error("⚠️ لم يتم العثور على مفتاح API.")

model_choice = st.selectbox("اختر الموديل:", [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
])

if st.button("🗑️ مسح الذاكرة"):
    st.session_state.chat_history = []
    st.rerun()

# عرض المحادثات السابقة
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# إدخال النص
query = st.text_area("اشرح الموقف الاستراتيجي:", height=120)

col1, col2 = st.columns(2)
btn_Classico = col1.button("🏛️ تفعيل بروتوكول Classico")
btn_L = col2.button("⚖️ قانوني (منفصل)")

# =============================================
# 4. PROCESSING LOGIC (The Classico Upgrade)
# =============================================
def run_classico(query):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_choice)

        # The Classico Master Prompt
        prompt = f"""
        أنت نظام 'The Classico' لإدارة الصراعات. الموقف: {query}.
        طبق القواعد الـ 18 (الهندسة العكسية، الضربة الثلاثية، البدائل المحكومة).
        
        قسم الرد بدقة إلى:
        ZONE_A: الملف القانوني (صيغة قانونية وشرعية للمحامي).
        ZONE_B: قبو الاستراتيجية (تحليل الجشع، اللاعبين الخفيين، والضغط النفسي للـ Chairman).
        """

        with st.status("⚔️ جاري تفعيل 'The Silent Fight'...", expanded=False) as status:
            st.write("🕵️ جاري تعقب Shadow Players...")
            res = model.generate_content(prompt)
            status.update(label="✅ اكتمل التحليل الاستراتيجي", state="complete")

        if res and res.text:
            # Parsing the two zones
            content = res.text
            za = content.split("ZONE_A:")[1].split("ZONE_B:")[0] if "ZONE_A:" in content else content
            zb = content.split("ZONE_B:")[1] if "ZONE_B:" in content else "لم يتم تحديد المنطقة الاستراتيجية."
            
            # Adding to your original chat_history list
            st.session_state.chat_history.append({"label": "⚖️ Zone A (قانوني)", "content": za, "style": "legal"})
            st.session_state.chat_history.append({"label": "🕵️ Zone B (القبو)", "content": zb, "style": "vault"})
            st.rerun()
            
    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")

if query and api_key:
    if btn_Classico:
        run_classico(query)
    elif btn_L:
        # Keeping your original logic for single roles if needed
        pass

# =============================================
# 5. OFFICIAL REPORT
# =============================================
if st.session_state.chat_history:
    st.divider()
    full_report = f"--- تقرير The Classico ---\nالتاريخ: {datetime.now()}\n\n"
    for c in st.session_state.chat_history:
        full_report += f"[{c['label']}]:\n{c['content']}\n\n"

    st.download_button("📥 تحميل التقرير الاستراتيجي", full_report.encode('utf-8'), "Report.txt")
