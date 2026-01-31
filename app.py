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
        word-wrap: break-word;
        white-space: normal;
    }
    .legal { border-color: #1d4ed8; background-color: #eff6ff; color: #1e3a8a; }
    .vault { border-color: #dc2626; background-color: #fef2f2; color: #7f1d1d; border-style: dashed; }
    .psych { border-color: #7c3aed; background-color: #f5f3ff; color: #2e1065; }
    .strat { border-color: #ea580c; background-color: #fffbeb; color: #451a03; }
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
st.title("🏛️ Project: The Classico")

api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    st.error("⚠️ API Key not found in Streamlit Secrets.")

# Updated to Gemini 2.5 stable versions
model_choice = st.selectbox("اختر الموديل الاستراتيجي:", [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
])

if st.button("🗑️ مسح الذاكرة"):
    st.session_state.chat_history = []
    st.rerun()

# عرض المحادثات السابقة
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# إدخال النص
query = st.text_area("اشرح الموقف الاستراتيجي (Raw Data):", height=120)

col1, col2, col3 = st.columns(3)
btn_Classico = col1.button("🏛️ بروتوكول Classico")
btn_L = col2.button("⚖️ قانوني")
btn_P = col3.button("🧠 نفسي")

# =============================================
# 4. PROCESSING LOGIC
# =============================================
def run_analysis(role_type, query):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_choice)

        if role_type == "classico":
            prompt = f"""
            أنت نظام 'The Classico'. الموقف: {query}.
            طبق 'القواعد الـ 18' (الهندسة العكسية، الضربة الثلاثية، البدائل المحكومة).
            
            قسم الرد إلى:
            ZONE_A: الملف القانوني (صياغة شرعية وعقارية رصينة).
            ZONE_B: قبو الاستراتيجية (تحليل الجشع، Shadow Players، وخطة الضغط).
            """
        elif role_type == "legal":
            prompt = f"أنت محامي ذكي خبير في قوانين المواريث والعقارات. حلل الموقف قانونياً: {query}"
        else:
            prompt = f"أنت خبير تحليل نفسي جنائي. حدد نقاط الضعف والجشع في الأطراف التالية: {query}"

        with st.status("⚔️ جاري تفعيل 'The Silent Fight'...", expanded=False) as status:
            res = model.generate_content(prompt)
            status.update(label="✅ اكتملت العملية الاستراتيجية", state="complete")

        if res and res.text:
            text = res.text
            if role_type == "classico" and "ZONE_B:" in text:
                za = text.split("ZONE_A:")[1].split("ZONE_B:")[0].strip()
                zb = text.split("ZONE_B:")[1].strip()
                st.session_state.chat_history.append({"label": "⚖️ Zone A: القانوني", "content": za, "style": "legal"})
                st.session_state.chat_history.append({"label": "🕵️ Zone B: القبو", "content": zb, "style": "vault"})
            else:
                label = "⚖️ القانوني" if role_type == "legal" else "🧠 النفسي"
                style = "legal" if role_type == "legal" else "psych"
                st.session_state.chat_history.append({"label": label, "content": text, "style": style})
            st.rerun()

    except Exception as e:
        st.error(f"⚠️ خطأ في النظام: {e}")

if query and api_key:
    if btn_Classico:
        run_analysis("classico", query)
    elif btn_L:
        run_analysis("legal", query)
    elif btn_P:
        run_analysis("psych", query)

# =============================================
# 5. OFFICIAL REPORT
# =============================================
if st.session_state.chat_history:
    st.divider()
    full_report = f"--- تقرير Strategic War Room ---\nالتاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    for c in st.session_state.chat_history:
        full_report += f"[{c['label']}]:\n{c['content']}\n{'-'*30}\n"

    st.download_button(
        label="📥 تحميل التقرير الرسمي",
        data=full_report.encode('utf-8'),
        file_name=f"The_Classico_Report_{datetime.now().strftime('%y%m%d')}.txt",
        mime="text/plain"
    )
