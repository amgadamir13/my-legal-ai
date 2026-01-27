import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import io
import traceback
import re
from typing import List

# --------------------
# إعداد الصفحة وCSS
# --------------------
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* اجعل التفاف الكلمات والسلوك الافتراضي آمناً للغات المتصلة (العربية) */
    .stMarkdown p, .stMarkdown div {
        display: block !important;
        white-space: pre-wrap !important;
        word-break: normal !important;
        overflow-wrap: break-word !important;
        min-width: 320px !important;
    }

    .msg-box {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        line-height: 1.8;
        border-right: 12px solid;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        width: 100% !important;
        background-color: #ffffff;
        display: block !important;
    }

    .user-style { border-color: #1e3a8a; background-color: #f8fafc; color: #1e3a8a; }
    .ai-style { border-color: #10b981; background-color: #f0fdf4; color: #14532d; }

    .finding-card {
        background: #ffffff; padding: 25px; border-radius: 15px;
        margin-bottom: 20px; border-right: 8px solid #cbd5e1;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        display: block !important;
        width: 100% !important;
        word-break: normal !important;
    }

    input[type="password"] { direction: ltr !important; text-align: left !important; }
    .stButton button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background-color: #1e3a8a; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------
# حالة الجلسة
# --------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "raw_last_response" not in st.session_state:
    st.session_state.raw_last_response = None

# --------------------
# الشريط الجانبي (الـ Vault)
# --------------------
with st.sidebar:
    st.title("🛡️ المحقق الاستراتيجي")
    api_key = st.text_input(
        "مفتاح Gemini السري:",
        type="password",
        placeholder="أدخل API Key الخاص بـ Gemini هنا",
    )
    st.markdown("`model:` قابل للتغيير أدناه (إن لم تكن متأكداً غيّر الاسم بعد تجربة list_models)")
    model_name = st.text_input("اسم النموذج (Model name):", value="gemini-1.5-flash")
    st.divider()
    v_files = st.file_uploader("قبو الحقائق (Vault):", accept_multiple_files=True)
    o_files = st.file_uploader("ملفات الخصم (Opponent):", accept_multiple_files=True)
    show_raw = st.checkbox("عرض الاستجابة الخام (debug)", value=False)
    if st.button("تفريغ الذاكرة 🗑️"):
        st.session_state.chat_history = []
        st.session_state.raw_last_response = None
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# --------------------
# مساعدة: تنظيف/تطبيع نص عربي مستخرج من PDF
# --------------------
def normalize_arabic_text(text: str) -> str:
    """
    يقوم بما يلي لتقليل مشكلة الحروف المتقطعة/المكدسة:
      - يزيل zero-width non-joiner/joiner (U+200C, U+200D)
      - يزيل المسافات أو الأسطر بين الحروف العربية (يعيد ربطها)
      - يقلص الفراغات المتكررة ويحافظ على فواصل الفقرات المعقولة
    """
    if not text:
        return ""
    # إزالة zero-width joiner/non-joiner
    text = text.replace("\u200c", "").replace("\u200d", "")
    # امسح الأسطر أو الفراغات بين الحروف العربية حتى لا تظهر منفصلة
    text = re.sub(r'(?<=[\u0600-\u06FF])\s*\n\s*(?=[\u0600-\u06FF])', '', text)
    text = re.sub(r'(?<=[\u0600-\u06FF])\s+(?=[\u0600-\u06FF])', '', text)
    # تقليص فراغات غير ضرورية (حافظ على فقرتين كحد أقصى)
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t\f\v]{2,}', ' ', text)
    return text.strip()

# --------------------
# مساعدة: استخراج نص من ملفات PDF (PyMuPDF)
# --------------------
def get_text_from_files(files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> str:
    text = ""
    if not files:
        return ""
    for f in files:
        try:
            raw = f.read()
            if not raw:
                continue
            # افصل المحاولة لأن fitz قد يرفع استثناء لملفات غير pdf
            with fitz.open(stream=raw, filetype="pdf") as doc:
                for page in doc:
                    page_text = page.get_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as ex:
            # تخطي الملفات غير الصحيحة، تابع باقي الملفات
            # عرض الاستثناء أثناء التصحيح حتى نعرف سبب الفشل
            try:
                if show_raw:
                    st.error(f"خطأ عند قراءة الملف: {getattr(f, 'name', 'uploaded_file')}")
                    st.exception(ex)
            except Exception:
                pass
            continue
    # طابق/نظف نصوص اللغة العربية المحتملة قبل الإرجاع
    return normalize_arabic_text(text)

# --------------------
# مساعدة: استخراج النص من شكل الاستجابة المتغير لـ Gemini
# --------------------
def extract_text_from_response(resp) -> str:
    """
    يحاول استخراج نص الإنسان القابل للقراءة من الأشكال المختلفة للاستجابة.
    يدعم: كائنات مع candidates/candidates[0].content، output، text، dict-like responses.
    """
    try:
        if resp is None:
            return ""
        if hasattr(resp, "candidates") and resp.candidates:
            cand = resp.candidates[0]
            if hasattr(cand, "content") and cand.content:
                return cand.content
            if hasattr(cand, "text") and cand.text:
                return cand.text
            return str(cand)
        if hasattr(resp, "output_text") and resp.output_text:
            return resp.output_text
        if hasattr(resp, "output") and resp.output:
            out = resp.output
            if isinstance(out, str):
                return out
            try:
                return str(out)
            except Exception:
                pass
        if hasattr(resp, "text") and resp.text:
            return resp.text
        if isinstance(resp, dict):
            cands = resp.get("candidates")
            if cands and isinstance(cands, list) and len(cands) > 0:
                first = cands[0]
                if isinstance(first, dict):
                    return first.get("content") or first.get("text") or str(first)
                return str(first)
            return resp.get("output") or resp.get("output_text") or resp.get("text") or str(resp)
        return str(resp)
    except Exception:
        return f"<unable to extract text: {traceback.format_exc()}>"

# --------------------
# استدعاء Gemini بأكثر من مدخل محتمل (متوافق مع إصدارات مختلفة من المكتبة)
# نسخة محسّنة تُحاول أيضًا استرداد قائمة النماذج لاقتراح أسماء صالحة
# --------------------
def call_gemini(prompt: str, model_name: str = "gemini-
