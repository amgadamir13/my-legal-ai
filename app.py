# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import re
import time
from datetime import datetime

# =============================================
# 1. PAGE CONFIGURATION & STYLING
# =============================================
st.set_page_config(page_title="War Room Audit", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Cairo', sans-serif !important;
    unicode-bidi: bidi-override !important;
    writing-mode: horizontal-tb !important;
}
* {
    word-break: normal !important;
    white-space: normal !important;
    line-height: 1.8 !important;
}
.msg-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-right: 6px solid; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
.user-style { border-color: #1e3a8a; background: #f1f5f9; color: #1e3a8a; }
.response-style { border-color: #059669; background: #ecfdf5; color: #064e3b; }
</style>
""", unsafe_allow_html=True)

# =============================================
# 2. UTILITIES
# =============================================
def normalize_arabic_text(text: str) -> str:
    if not text: return ""
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', text)
    replacements = {'أ':'ا','إ':'ا','آ':'ا','ة':'ه'}
    for old,new in replacements.items(): text = text.replace(old,new)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_text_from_pdf(file_bytes, max_pages=20):
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for i, page in enumerate(doc):
            if i >= max_pages:
                text += "\n[تم الاقتصار على أول 20 صفحة]"
                break
            text += page.get_text() + "\n"
    return normalize_arabic_text(text)

def get_text_from_files(files):
    if not files: return ""
    all_text = []
    for file in files:
        if file.type != "application/pdf": continue
        file.seek(0)
        text = extract_text_from_pdf(file.read())
        if text: all_text.append(f"--- ملف: {file.name} ---\n{text}\n")
    return "\n".join(all_text)

# =============================================
# 3. SESSION STATE
# =============================================
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "last_request_time" not in st.session_state: st.session_state.last_request_time = 0

# =============================================
# 4. SIDEBAR
# =============================================
with st.sidebar:
    st.header("🛡️ الإعدادات")
    model_choice = st.selectbox("اختر النموذج:", ["gemini-3-flash","gemini-3-pro"])
    files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)

# =============================================
# 5. MAIN INTERFACE
# =============================================
st.title("⚖️ War Room Audit Report")
user_query = st.text_area("🎯 صف الموقف الحالي:", height=120)

col1,col2 = st.columns(2)
btn_analyze = col1.button("🔍 تحليل شامل")
btn_clear = col2.button("🗑️ مسح السجل")

if btn_clear:
    st.session_state.chat_history = []
    st.rerun()

# =============================================
# 6. EXECUTION LOGIC
# =============================================
def run_analysis(query, docs_text):
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 2:
        st.warning("⏳ انتظر ثانيتين بين الطلبات")
        return
    st.session_state.last_request_time = current_time

    # ✅ API key from secrets
    api_key = st.secrets["general"]["GEMINI_API_KEY"]

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_choice)

        prompt = f"""
أنت فريق متعدد التخصصات في غرفة الحرب القانونية.
الموقف: {query}
الوثائق: {docs_text or "لا توجد"}

أنتج تقريراً منظماً يتضمن:
1. ملخص تنفيذي.
2. رأي المحامي الذكي (Street Smart Lawyer) الموالي للعميل.
3. رأي محامي الخصم (Defense Counsel).
4. رأي خبير قانون الإيجار المصري.
5. رأي المحلل النفسي.
6. رأي الشرطي.
7. رأي المجرم السابق.
8. مراجعة المدقق (Audit Review).
9. توصيات نهائية عملية.

استخدم لغة قانونية دقيقة، مصطلحات صحيحة، وتنظيم رسمي كما في المذكرات والمحاضر.
        """

        with st.spinner("🤖 جاري التحليل..."):
            res = model.generate_content(prompt)

        if res and res.text:
            st.session_state.chat_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "query": query,
                "response": res.text
            })
            st.rerun()
        else:
            st.error("لم يتم توليد رد")
    except Exception as e:
        st.error(f"❌ خطأ: {e}")

if user_query and btn_analyze:
    docs_text = get_text_from_files(files)
    run_analysis(user_query, docs_text)

# =============================================
# 7. DISPLAY CHAT HISTORY
# =============================================
if st.session_state.chat_history:
    st.subheader("📜 سجل التحليلات")
    for chat in reversed(st.session_state.chat_history[-10:]):
        st.markdown(f'''
        <div class="msg-box user-style">
            <b>👤 سؤالك:</b> {chat['query']}
            <br><small>{chat['timestamp']}</small>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="msg-box response-style">
            <b>📋 التقرير:</b><br>{chat['response']}
        </div>
        ''', unsafe_allow_html=True)

    # Download report
    report_text = "\n\n".join(
        [f"سؤال: {c['query']}\nوقت: {c['timestamp']}\nرد:\n{c['response']}" for c in st.session_state.chat_history]
    )
    st.download_button("📥 تنزيل التقرير", report_text, file_name="WarRoom_Report.txt", mime="text/plain")

else:
    st.info("✍️ اكتب موقفك واضغط على زر التحليل لبدء العمل.")
