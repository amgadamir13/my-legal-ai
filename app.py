import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io

# --- 1. الهوية البصرية والقضاء على مشكلة الحروف العمودية ---
st.set_page_config(page_title="Legal Strategic Vault", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* فرض التنسيق الأفقي ومنع انكسار الكلمات */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] p {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: normal !important;
        word-break: keep-all !important; /* يمنع تحول الكلمة لحروف عمودية */
        overflow-wrap: break-word !important;
    }

    /* تحسين فقاعات الشات */
    .msg-box { 
        padding: 20px; border-radius: 15px; margin-bottom: 15px; 
        line-height: 1.8; border-right: 8px solid; 
        width: 100% !important; display: block !important;
    }
    .user-style { background-color: #f1f5f9; border-color: #1e3a8a; color: #1e3a8a; }
    .legal-style { background-color: #f0fdf4; border-color: #10b981; color: #166534; }
    .psych-style { background-color: #f5f3ff; border-color: #8b5cf6; color: #4c1d95; }
    .street-style { background-color: #fff1f2; border-color: #f43f5e; color: #9f1239; }

    /* بطاقات النتائج الرسمية */
    .finding-card {
        background: white; padding: 15px; border-radius: 12px;
        margin-bottom: 10px; border-left: 5px solid #cbd5e1;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 3. القائمة الجانبية ---
with st.sidebar:
    st.header("🛡️ مركز القيادة")
    api_key = st.text_input("مفتاح Gemini:", type="password")
    v_files = st.file_uploader("قبو حقائقي (Vault)", accept_multiple_files=True)
    o_files = st.file_uploader("ملفات الخصم (Opponent)", accept_multiple_files=True)
    if st.button("تفريغ الذاكرة 🗑️"):
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ المحقق الاستراتيجي")

# --- 4. محرك العقول الثلاثة ---
with st.form("war_room_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف الحالي هنا...", height=120)
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

if (btn_L or btn_P or btn_S) and api_key and user_query:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if btn_L: role, label, style = "محامي خبير", "⚖️ القانوني", "legal-style"
        elif btn_P: role, label, style = "محلل نفسي جنائي", "🧠 النفسي", "psych-style"
        else: role, label, style = "مفاوض استراتيجي داهية", "🧨 الداهية", "street-style"

        # قراءة الملفات (دعم كامل لكافة الصفحات)
        v_txt = ""
        if v_files:
            for f in v_files:
                with fitz.open(stream=f.read(), filetype="pdf") as doc:
                    for p in doc: v_txt += p.get_text()
        
        prompt = f"تقمص دور {role}. حقائقي: {v_txt[:10000]}. السؤال: {user_query}"
        
        with st.spinner("جاري التحليل..."):
            response = model.generate_content(prompt)
            st.session_state.chat_history.append({"label": label, "content": response.text, "style": style, "role": "ai"})
            st.rerun()
    except Exception as e:
        st.error(f"خطأ: {e}")

# --- 5. عرض المحادثة ---
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}:</b><br>{chat["content"]}</div>', unsafe_allow_html=True)

# --- 6. قسم النتائج الرسمية (تصميم البطاقات الأفقي) ---
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    
    st.markdown("""
        <div class="finding-card" style="border-right: 5px solid #3b82f6;">
            <b>⚖️ الثغرات المستخرجة:</b><br>جاري فحص التناقضات المادية في التواريخ والأسماء.
        </div>
        <div class="finding-card" style="border-right: 5px solid #f59e0b;">
            <b>🧠 نمط الخصم:</b><br>تحديد نقاط الضعف النفسية بناءً على لغة المستندات.
        </div>
        <div class="finding-card" style="border-right: 5px solid #10b981;">
            <b>🎯 الخطوة القادمة:</b><br>تجهيز الرد الاستراتيجي بناءً على التحليل المختار.
        </div>
    """, unsafe_allow_html=True)
