import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import io
import traceback
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

    .stMarkdown p, .stMarkdown div {
        display: block !important;
        white-space: pre-wrap !important;
        word-break: keep-all !important;
        overflow-wrap: normal !important;
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
        display: inline-block !important;
    }

    .user-style { border-color: #1e3a8a; background-color: #f8fafc; color: #1e3a8a; }
    .ai-style { border-color: #10b981; background-color: #f0fdf4; color: #14532d; }

    .finding-card {
        background: #ffffff; padding: 25px; border-radius: 15px;
        margin-bottom: 20px; border-right: 8px solid #cbd5e1;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        display: block !important;
        width: 100% !important;
        word-break: keep-all !important;
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
    st.markdown("`model:` gemini-1.5-flash (قابل للتغيير داخل الكود)")
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
        except Exception:
            # تخطي الملفات غير الصحيحة، تابع باقي الملفات
            continue
    return text.strip()

# --------------------
# مساعدة: استخراج النص من شكل الاستجابة المتغير لـ Gemini
# --------------------
def extract_text_from_response(resp) -> str:
    """
    يحاول استخراج نص الإنسان القابل للقراءة من الأشكال المختلفة للاستجابة.
    يدعم: كائنات مع candidates/candidates[0].content، output، text، dict-like responses.
    """
    try:
        # object-like patterns
        if resp is None:
            return ""
        # Some clients return an object with .candidates list
        if hasattr(resp, "candidates") and resp.candidates:
            cand = resp.candidates[0]
            # candidate may expose .content or .text
            if hasattr(cand, "content") and cand.content:
                return cand.content
            if hasattr(cand, "text") and cand.text:
                return cand.text
            # fallback to str
            return str(cand)
        # Many variants use resp.output or resp.output_text or resp.text
        if hasattr(resp, "output_text") and resp.output_text:
            return resp.output_text
        if hasattr(resp, "output") and resp.output:
            # sometimes output is a string, sometimes list/dict
            out = resp.output
            if isinstance(out, str):
                return out
            try:
                return str(out)
            except Exception:
                pass
        if hasattr(resp, "text") and resp.text:
            return resp.text
        # dict-like responses
        if isinstance(resp, dict):
            # candidates -> {content|text}
            cands = resp.get("candidates")
            if cands and isinstance(cands, list) and len(cands) > 0:
                first = cands[0]
                if isinstance(first, dict):
                    return first.get("content") or first.get("text") or str(first)
                return str(first)
            # other keys
            return resp.get("output") or resp.get("output_text") or resp.get("text") or str(resp)
        # last resort
        return str(resp)
    except Exception:
        return f"<unable to extract text: {traceback.format_exc()}>"

# --------------------
# استدعاء Gemini بأكثر من مدخل محتمل (متوافق مع إصدارات مختلفة من المكتبة)
# --------------------
def call_gemini(prompt: str, model_name: str = "gemini-1.5-flash", api_key: str = None):
    """
    يحاول عدة واجهات شائعة للمكتبة google.generativeai:
      - genai.generate_text(...)
      - genai.generate(...)
      - genai.GenerativeModel(...).generate_content(...)
    ويعيد كائن الاستجابة الخام بالإضافة إلى النص المستخرج.
    قد تحتاج لتعديل هذا الدالة لتطابق إصدار الحزمة لديك.
    """
    if not api_key:
        raise ValueError("API key is required for Gemini")

    genai.configure(api_key=api_key)

    # محاولة استدعاءات مختلفة حسب توفر الواجهة
    resp = None
    last_err = None
    try:
        if hasattr(genai, "generate_text"):
            # modern SDK surface (example)
            resp = genai.generate_text(model=model_name, prompt=prompt)
            return resp, extract_text_from_response(resp)
    except Exception as e:
        last_err = e

    try:
        if hasattr(genai, "generate"):
            # alternative API surface
            resp = genai.generate(model=model_name, prompt=prompt)
            return resp, extract_text_from_response(resp)
    except Exception as e:
        last_err = e

    try:
        # older/alternate pattern seen in some examples
        if hasattr(genai, "GenerativeModel"):
            mdl = genai.GenerativeModel(model_name)
            # some older examples use generate_content(prompt)
            if hasattr(mdl, "generate_content"):
                resp = mdl.generate_content(prompt)
                return resp, extract_text_from_response(resp)
            # fallback to other method names if present
            if hasattr(mdl, "generate"):
                resp = mdl.generate(prompt)
                return resp, extract_text_from_response(resp)
    except Exception as e:
        last_err = e

    # إن وصلت هنا فواجهنا خطأ في كل الطرق
    raise RuntimeError(f"لم أجد واجهة مدعومة في google.generativeai أو جميع الاستدعاءات فشلت. آخر خطأ: {last_err}")

# --------------------
# النموذج وواجهة المستخدم
# --------------------
with st.form("war_room_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف الحالي هنا:", height=120)
    c1, c2, c3 = st.columns(3)
    with c1:
        btn_L = st.form_submit_button("⚖️ قانوني")
    with c2:
        btn_P = st.form_submit_button("🧠 نفسي")
    with c3:
        btn_S = st.form_submit_button("🧨 داهية")

if (btn_L or btn_P or btn_S):
    if not api_key:
        st.error("الرجاء إدخال مفتاح Gemini في الشريط الجانبي.")
    elif not user_query or user_query.strip() == "":
        st.error("أدخل نص السؤال/الحالة في الحقل الرئيسي قبل الإرسال.")
    else:
        # إعداد السياق من الملفات
        v_context = get_text_from_files(v_files if v_files else [])
        o_context = get_text_from_files(o_files if o_files else [])

        # تقييد طول السياق حفاظاً على حدود التوكين
        MAX_CONTEXT_CHARS = 30000  # اضبط حسب الحد المسموح به
        v_ctx_snippet = v_context[:MAX_CONTEXT_CHARS]
        o_ctx_snippet = o_context[:MAX_CONTEXT_CHARS]

        identity = "⚖️ القانوني" if btn_L else ("🧠 النفسي" if btn_P else "🧨 الداهية")
        style = "ai-style"

        # بناء البرومبت بصيغة واضحة ومحددة
        prompt = (
            "أنت مستشار استراتيجي قانوني/نفسي/تفاوضي ذو خبرة. "
            "اقرأ المعلومات التال��ة ثم أجب بدقة وبصيغة عملية مع نقاط قابلة للتنفيذ.\n\n"
            f"الهوية المطلوبة: {identity}\n\n"
            f"الحقائق (Vault):\n{v_ctx_snippet}\n\n"
            f"ملفات الخصم (Opponent):\n{o_ctx_snippet}\n\n"
            f"السؤال/المطلوب: {user_query}\n\n"
            "أدرج: (1) نقاط القوة/الضعف القانونية أو النفسية، (2) استراتيجيات مقترحة، (3) خطوات تنفيذية قصيرة المدى، "
            "و (4) ملاحظات عن المخاطر المحتملة. كن موجزاً ومنظماً باستخدام عناوين وقوائم."
        )

        try:
            with st.spinner("جاري استدعاء Gemini — انتظر قليلاً..."):
                raw_resp, answer_text = call_gemini(prompt=prompt, model_name="gemini-1.5-flash", api_key=api_key)
                # سجل الاستجابة الخام والمتنقّى
                st.session_state.raw_last_response = raw_resp
                st.session_state.chat_history.append(
                    {"q": user_query, "a": answer_text, "label": identity, "style": style}
                )
                # أعد تحميل الواجهة لعرض النتيجة الجديدة
                st.rerun()
        except Exception as e:
            # عرض خطأ واضح + تتبع الاستثناء للمساعدة في التصحيح
            st.error(f"حدث خطأ أثناء استدعاء Gemini: {e}")
            st.exception(traceback.format_exc())

# --------------------
# عرض المحادثة
# --------------------
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box user-style"><b>👤 أنت:</b><br>{chat["q"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="msg-box ai-style"><b>{chat["label"]}:</b><br>{chat["a"]}</div>', unsafe_allow_html=True)

# --------------------
# تقرير نهائي وRaw response (اختياري)
# --------------------
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    st.markdown(
        """
        <div class="finding-card">
            <b style="color: #1e3a8a;">⚖️ الثغرات المستخرجة:</b><br>
            تم تحليل البيانات وستظهر النتائج هنا بشكل أفقي سليم تماماً.
        </div>
        <div class="finding-card" style="border-right-color: #8b5cf6;">
            <b style="color: #8b5cf6;">🧠 نمط الخصم:</b><br>
            تحليل التناقضات السلوكية في الملفات المرفوعة.
        </div>
        """,
        unsafe_allow_html=True,
    )

if show_raw and st.session_state.raw_last_response is not None:
    with st.expander("عرض الاستجابة الخام (raw)"):
        st.write(st.session_state.raw_last_response)
