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
    .psych { border-color: #7c3aed; background-color: #f5f3ff; color: #2e1065; }
    .strat { border-color: #ea580c; background-color: #fffbeb; color: #451a03; }
    .combo { border-color: #059669; background-color: #ecfdf5; color: #064e3b; }
    .creative { border-color: #9333ea; background-color: #faf5ff; color: #4c1d95; }
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
query = st.text_area("اشرح الموقف الاستراتيجي:", height=120)

col1, col2, col3, col4, col5 = st.columns(5)
btn_L = col1.button("⚖️ قانوني")
btn_P = col2.button("🧠 نفسي")
btn_S = col3.button("🧨 استراتيجي")
btn_C = col4.button("🔀 تحليل شامل")
btn_B = col5.button("💡 إبداعي")

# =============================================
# 4. PROCESSING LOGIC
# =============================================
def run_analysis(role, label, style, query):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_choice)

        # Prompt with clarification rule
        prompt = f"""
أنت {role}.
الموقف: {query}.
إذا لم تكن المعلومات مؤكدة بنسبة 100%، اطلب توضيح من المستخدم بدلاً من الافتراض.
أجب بالعربية بأسلوب منظم.
ابدأ بـ **الملخص التنفيذي**.
ثم قسم الرد إلى:
- الوقائع
- القضايا المطروحة
- التحليل
- الاستنتاج
أضف نصائح عملية وذكية (street-smart) إذا كان الدور قانوني.
        """

        with st.spinner("⚔️ جاري التحليل..."):
            res = model.generate_content(prompt)

        if res and res.text:
            st.session_state.chat_history.append({
                "label": label,
                "content": res.text,
                "style": style
            })
            st.rerun()
        else:
            st.error("لم يتم توليد رد من النموذج.")
    except gapi_errors.ResourceExhausted:
        st.error("⚠️ انتهت الحصة المجانية لهذا الموديل. جرب تبديل الموديل أو انتظر قليلاً.")
    except Exception as e:
        st.error(f"⚠️ خطأ في النظام: {e}")

if query and api_key:
    if btn_L:
        run_analysis("محامي ذكي يجمع بين التحليل القانوني والمشورة العملية", "⚖️ القانوني", "legal", query)
    elif btn_P:
        run_analysis("محلل نفسي وخبير تفاوض", "🧠 النفسي", "psych", query)
    elif btn_S:
        run_analysis("مخطط استراتيجي داهية", "🧨 الاستراتيجي", "strat", query)
    elif btn_C:
        run_analysis("خبير يجمع بين القانون وعلم النفس والاستراتيجية", "🔀 التحليل الشامل", "combo", query)
    elif btn_B:
        run_analysis("مفكر إبداعي يقدم أفكار غير تقليدية", "💡 الإبداعي", "creative", query)

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
