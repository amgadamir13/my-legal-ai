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
st.set_page_config(page_title="Strategic War Room Pro", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Cairo', sans-serif !important;
}
.msg-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-right: 6px solid; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
.user-style { border-color: #1e3a8a; background: #f1f5f9; color: #1e3a8a; }
.legal { border-color: #3b82f6; background: #eff6ff; color: #1e40af; }
.psych { border-color: #8b5cf6; background: #f5f3ff; color: #4c1d95; }
.strat { border-color: #f59e0b; background: #fffbeb; color: #78350f; }
.combo { border-color: #059669; background: #ecfdf5; color: #064e3b; }
.creative { border-color: #9333ea; background: #faf5ff; color: #4c1d95; }
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

def extract_text_from_pdf(file_bytes, max_pages=30):
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for i, page in enumerate(doc):
            if i >= max_pages:
                text += "\n[تم الاقتصار على أول 30 صفحة]"
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
if "analysis_count" not in st.session_state: st.session_state.analysis_count = 0
if "last_request_time" not in st.session_state: st.session_state.last_request_time = 0

# =============================================
# 4. SIDEBAR
# =============================================
with st.sidebar:
    st.header("🛡️ مركز القيادة")
    try:
        default_api_key = st.secrets["GEMINI_API_KEY"]
        api_key = st.text_input("🔑 مفتاح Gemini API:", value=default_api_key, type="password")
    except:
        api_key = st.text_input("🔑 مفتاح Gemini API:", type="password")

    model_choice = st.selectbox("اختر النموذج:", ["gemini-3-flash","gemini-3-pro","gemini-2.5-flash","gemini-2.5-pro"])

    v_files = st.file_uploader("📂 وثائقنا (Vault)", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ وثائق الخصم", type=["pdf"], accept_multiple_files=True)

    if st.button("🗑️ تفريغ الذاكرة"):
        st.session_state.chat_history = []
        st.session_state.analysis_count = 0
        st.rerun()

    st.metric("عدد التحليلات", st.session_state.analysis_count)
    st.metric("الملفات المرفوعة", len(v_files or []) + len(o_files or []))
    st.metric("آخر تحديث", datetime.now().strftime("%H:%M"))

# =============================================
# 5. MAIN INTERFACE
# =============================================
st.title("⚖️ Strategic War Room Pro")
user_query = st.text_area("🎯 وصف الموقف الحالي:", height=120)

col1,col2,col3,col4,col5 = st.columns(5)
btn_L = col1.button("⚖️ قانوني")
btn_P = col2.button("🧠 نفسي")
btn_S = col3.button("🧨 استراتيجي")
btn_C = col4.button("🔀 شامل")
btn_B = col5.button("💡 إبداعي")

# =============================================
# 6. EXECUTION LOGIC
# =============================================
def run_analysis(role,label,style,query,vault_text,opponent_text):
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 2:
        st.warning("⏳ انتظر ثانيتين بين الطلبات")
        return
    st.session_state.last_request_time = current_time

    if not api_key or len(api_key.strip())<20:
        st.error("⚠️ مفتاح API غير صالح")
        return

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_choice)

        prompt = f"""
أنت {role}.
الموقف: {query}.
وثائقنا: {vault_text or "لا توجد"}
وثائق الخصم: {opponent_text or "لا توجد"}
إذا لم تكن المعلومات مؤكدة بنسبة 100%، اطلب توضيح من المستخدم.
ابدأ بـ الملخص التنفيذي، ثم الوقائع، القضايا، التحليل، الاستنتاج.
أضف نصائح عملية وذكية إذا كان الدور قانوني.
        """

        with st.spinner("🤖 جاري التحليل..."):
            res = model.generate_content(prompt)

        if res and res.text:
            st.session_state.chat_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "label": label,
                "style": style,
                "query": query,
                "response": res.text,
                "files_count": len(v_files or [])+len(o_files or [])
            })
            st.session_state.analysis_count += 1
            st.rerun()
        else:
            st.error("لم يتم توليد رد")
    except Exception as e:
        st.error(f"❌ خطأ: {e}")

if user_query and api_key:
    vault_text = get_text_from_files(v_files)
    opponent_text = get_text_from_files(o_files)
    if btn_L: run_analysis("محامي ذكي يجمع بين التحليل القانوني والمشورة العملية","⚖️ القانوني","legal",user_query,vault_text,opponent_text)
    elif btn_P: run_analysis("محلل نفسي وخبير تفاوض","🧠 النفسي","psych",user_query,vault_text,opponent_text)
    elif btn_S: run_analysis("مخطط استراتيجي داهية","🧨 الاستراتيجي","strat",user_query,vault_text,opponent_text)
    elif btn_C: run_analysis("خبير يجمع بين القانون وعلم النفس والاستراتيجية","🔀 التحليل الشامل","combo",user_query,vault_text,opponent_text)
    elif btn_B: run_analysis("مفكر إبداعي يقدم أفكار غير تقليدية","💡 الإبداعي","creative",user_query,vault_text,opponent_text)

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
        <div class="msg-box {chat['style']}">
            <b>{chat['label']}:</b><br>{chat['response']}
        </div>
        ''', unsafe_allow_html=True)

        # =============================================
    # 8. OFFICIAL FINDINGS SECTION
    # =============================================
    st.markdown("---")
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")

    all_analyses = []
    for chat in st.session_state.chat_history:
        all_analyses.append(f"""
        {'='*60}
        التحليل: {chat['label']}
        الوقت: {chat['timestamp']}
        {'='*60}

        السؤال: {chat['query']}

        الرد:
        {chat['response']}
        """)

    report_text = f"""
    التقرير الاستراتيجي النهائي
    تاريخ الإنشاء: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    عدد التحليلات: {len(st.session_state.chat_history)}
    {'='*80}

    {''.join(all_analyses)}

    {'='*80}
    الخلاصة:
    - راجع كل تحليل للتفاصيل الكاملة
    - استخدم النقاط القانونية كأساس للمرافعة
    - طبق الاستراتيجيات النفسية في التفاوض
    - تبنى الخطط التكتيكية المقترحة
    """

    st.download_button(
        label="📥 تنزيل التقرير",
        data=report_text,
        file_name=f"Strategic_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )

    # Summary Statistics
    st.markdown("#### 📊 إحصائيات التحليل")
    summary_cols = st.columns(4)
    analysis_types = [chat['style'] for chat in st.session_state.chat_history]

    with summary_cols[0]:
        st.metric("التحليلات القانونية", analysis_types.count("legal"))
    with summary_cols[1]:
        st.metric("التحليلات النفسية", analysis_types.count("psych"))
    with summary_cols[2]:
        st.metric("التحليلات الاستراتيجية", analysis_types.count("strat"))
    with summary_cols[3]:
        total_files = sum(chat['files_count'] for chat in st.session_state.chat_history)
        st.metric("إجمالي الملفات المعالجة", total_files)

# =============================================
# 9. EMPTY STATE
# =============================================
else:
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 40px; background: #f1f5f9; border-radius: 20px;">
        <h2 style="color: #1e3a8a;">🚀 مرحباً بكم في War Room Pro</h2>
        <p style="font-size: 18px; color: #64748b;">
        ابدأ برفع الوثائق في الشريط الجانبي، ثم اكتب سؤالك واختر نوع التحليل
        </p>
        <div style="display: flex; justify-content: space-around; margin-top: 30px;">
            <div style="padding: 20px; background: white; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
                <h3>⚖️ قانوني</h3><p>تحليل الجوانب القانونية والسوابق</p>
            </div>
            <div style="padding: 20px; background: white; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
                <h3>🧠 نفسي</h3><p>فهم الدوافع والتأثير النفسي</p>
            </div>
            <div style="padding: 20px; background: white; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
                <h3>🧨 استراتيجي</h3><p>تطوير خطط تكتيكية متقدمة</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================
# 10. FOOTER
# =============================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 20px;">
    <small>Strategic War Room Pro v2.0 | تم التطوير للاستخدام القانوني الاستراتيجي</small><br>
    <small>⚠️ هذا التطبيق مساعد فقط ولا يعد رأياً قانونياً ملزماً</small>
</div>
""", unsafe_allow_html=True)
