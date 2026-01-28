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
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important; 
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .msg-box { 
        padding: 20px; border-radius: 12px; margin-bottom: 15px; 
        border-right: 8px solid; background-color: #ffffff;
        box-shadow: 0 3px 8px rgba(0,0,0,0.08);
        width: 100%;
        word-wrap: break-word;
        white-space: normal;
    }
    
    .legal { border-color: #1d4ed8; background-color: #eff6ff; color: #1e3a8a; }
    .psych { border-color: #7c3aed; background-color: #f5f3ff; color: #2e1065; }
    .strat { border-color: #ea580c; background-color: #fffbeb; color: #451a03; }
    
    .stButton > button { width: 100%; font-weight: 700; height: 3em; border-radius: 8px; margin-top: 8px; }
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
    st.error("⚠️ لم يتم العثور على مفتاح API في الأسرار. أضفه في Streamlit باسم GEMINI_API_KEY.")

# ✅ قائمة الموديلات الصحيحة
model_choice = st.selectbox("اختر الموديل:", [
    "gemini-3-flash",
    "gemini-3-pro",
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
with st.form("strategic_form"):
    query = st.text_area("اشرح الموقف الاستراتيجي:", height=150)
    btn_L = st.form_submit_button("⚖️ قانوني")
    btn_P = st.form_submit_button("🧠 نفسي")
    btn_S = st.form_submit_button("🧨 استراتيجي")

# =============================================
# 4. PROCESSING LOGIC
# =============================================
if (btn_L or btn_P or btn_S):
    if not api_key:
        st.error("⚠️ يرجى إضافة مفتاح API في الأسرار أولاً.")
    elif not query:
        st.warning("⚠️ يرجى كتابة السؤال أو الموقف.")
    else:
        processing_placeholder = st.empty()
        with processing_placeholder.container():
            st.info("🔄 **تم استلام طلبك.** جاري التحليل...")

        try:
            # Configure Gemini
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_choice)

            # Role selection
            if btn_L:
                label, style, role = ("⚖️ القانوني", "legal", "خبير قانوني متخصص في الثغرات")
            elif btn_P:
                label, style, role = ("🧠 النفسي", "psych", "محلل نفسي وخبير تفاوض")
            else:
                label, style, role = ("🧨 الاستراتيجي", "strat", "مخطط استراتيجي داهية")

            # Structured legal memo style with Executive Summary
            prompt = f"""
أنت {role}.
الموقف: {query}.
أجب بالعربية بأسلوب مذكرة قانونية منظمة.
ابدأ بـ **الملخص التنفيذي** (فقرة قصيرة تلخص أهم النقاط).
ثم قسم الرد إلى:
- **الوقائع**
- **القضايا المطروحة**
- **التحليل**
- **الاستنتاج**
اكتب كل قسم في فقرة منفصلة بدون استخدام رموز خاصة مثل | * #.
            """

            with st.spinner("⚔️ جاري التحليل النهائي مع Gemini..."):
                res = model.generate_content(prompt)

            if res and res.text:
                st.session_state.chat_history.append({
                    "label": label,
                    "content": res.text,
                    "style": style
                })
                processing_placeholder.empty()
                st.rerun()
            else:
                st.error("لم يتم توليد رد من النموذج.")

        except gapi_errors.ResourceExhausted:
            processing_placeholder.empty()
            st.error("⚠️ انتهت الحصة المجانية لهذا الموديل. جرب تبديل الموديل أو انتظر قليلاً.")
        except Exception as e:
            processing_placeholder.empty()
            st.error(f"⚠️ خطأ في النظام: {e}")

# =============================================
# 5. OFFICIAL REPORT
# =============================================
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    
    full_report = f"--- تقرير Strategic War Room ---\nالتاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    for c in st.session_state.chat_history:
        full_report += f"[{c['label']}]:\n{c['content']}\n{'-'*30}\n"

    st.download_button(
        label="📥 تحميل التقرير الرسمي الكامل",
        data=full_report.encode('utf-8'),
        file_name=f"Strategic_Report_{datetime.now().strftime('%y%m%d_%H%M')}.txt",
        mime="text/plain"
    )
