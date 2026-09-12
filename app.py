# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions as gapi_errors
from datetime import datetime

# =============================================
# 1. PAGE SETUP & STYLING (Original Design)
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

# Updated to Gemini 2.5 stable versions
model_choice = st.selectbox("اختر الموديل الاستراتيجي:", [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
])

if st.button("🗑️ مسح الذاكرة"):
    st.session_state.chat_history = []
    st.rerun()

# Display History
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# Input
query = st.text_area("اشرح الموقف الاستراتيجي (Raw Data):", height=120)

col1, col2, col3 = st.columns(3)
btn_Classico = col1.button("🏛️ بروتوكول Classico")
btn_L = col2.button("⚖️ قانوني")
btn_P = col3.button("🧠 نفسي")
if btn_Classico:
    if not query.strip():
        st.warning("⚠️ الرجاء إدخال الموقف الاستراتيجي")
    else:
        run_analysis("classico", query)

elif btn_L:
    if not query.strip():
        st.warning("⚠️ الرجاء إدخال الموقف الاستراتيجي")
    else:
        run_analysis("legal", query)

elif btn_P:
    if not query.strip():
        st.warning("⚠️ الرجاء إدخال الموقف الاستراتيجي")
    else:
        run_analysis("psych", query)
# =============================================
# 4. PROCESSING LOGIC (Refactored Surgical Upgrade)
# =============================================

import re
from datetime import datetime

def build_prompt(role_type, query):
    prompts = {
        "classico": f"""
        أنت نظام 'The Classico'. الموقف: {query}.
        طبق 'القواعد الـ 18' (الهندسة العكسية، الضربة الثلاثية).
        
        قسم الرد إلى:
        ZONE_A: الملف القانوني (صياغة شرعية قضائية رصينة: حيث إن، بناءً عليه، الثابت يقيناً).
        ZONE_B: قبو الاستراتيجية (تحليل الجشع، Shadow Players، وخطة الضغط النفسي).
        """,
        "legal": f"""
        أنت 'المستشار القانوني' الخبير. تخصصك المواريث والعقارات.
        المطلوب: صياغة "مذكرة قانونية" للموقف: {query}.
        استخدم لغة قضائية شرعية صارمة (تكييف الوقائع، الأسانيد، والطلبات).
        """,
        "psych": f"""
        أنت خبير تحليل نفسي جنائي. حدد نقاط الضعف والجشع والـ Scapegoat في الموقف: {query}
        """
    }
    return prompts.get(role_type, prompts["psych"])


def parse_classico_response(text):
    """Extract Zone A and Zone B safely using regex."""
    match_a = re.search(r"ZONE_A:(.*?)(?=ZONE_B:)", text, re.DOTALL)
    match_b = re.search(r"ZONE_B:(.*)", text, re.DOTALL)
    return (
        match_a.group(1).strip() if match_a else None,
        match_b.group(1).strip() if match_b else None,
    )


def run_analysis(role_type, query):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_choice)

        prompt = build_prompt(role_type, query)

        with st.status("⚔️ جاري تفعيل غرف العمليات...", expanded=False) as status:
            res = model.generate_content(prompt)
            status.update(label="✅ اكتملت العملية", state="complete")

        if res and res.text:
            text = res.text

            if role_type == "classico":
                za, zb = parse_classico_response(text)
                if za:
                    st.session_state.chat_history.append(
                        {"label": "⚖️ Zone A: القانوني", "content": za, "style": "legal"}
                    )
                if zb:
                    st.session_state.chat_history.append(
                        {"label": "🕵️ Zone B: القبو", "content": zb, "style": "vault"}
                    )
            else:
                role_map = {
                    "legal": ("⚖️ القانوني", "legal"),
                    "psych": ("🧠 النفسي", "psych"),
                }
                label, style = role_map.get(role_type, ("🧠 النفسي", "psych"))
                st.session_state.chat_history.append({"label": label, "content": text, "style": style})

            st.rerun()

    except Exception as e:
        st.error(f"⚠️ خطأ أثناء التحليل: {str(e)}")


# =============================================
# 5. OFFICIAL REPORT (Refactored)
# =============================================
if st.session_state.chat_history:
    st.divider()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    header = f"--- تقرير Strategic War Room ---\nالتاريخ: {timestamp}\n\n"

    sections = [
        f"[{c['label']}]:\n{c['content']}\n{'-'*30}\n"
        for c in st.session_state.chat_history
    ]
    full_report = header + "".join(sections)

    st.download_button("📥 تحميل التقرير", full_report.encode('utf-8'), "Classico_Report.txt")
