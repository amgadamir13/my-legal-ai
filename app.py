import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io

# --- 1. الإعدادات النووية لمنع الحروف العمودية ---
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* فرض العرض الكامل ومنع انكسار الكلمات نهائياً */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* هذا الجزء يقتل مشكلة الحروف العمودية (م-ف-ت-ا-ح) */
    .msg-box { 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        line-height: 1.8; 
        border-right: 10px solid; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        width: 100% !important;
        display: block !important;
        white-space: normal !important; /* يمنع تحويل النص لعمود ضيق */
        word-break: keep-all !important; /* يمنع كسر الكلمة لحروف */
        min-width: 300px !important; /* يضمن مساحة أفقية كافية */
    }

    .user-style { background-color: #f8fafc; border-color: #1e3a8a; color: #1e3a8a; }
    .legal-style { background-color: #f0fdf4; border-color: #10b981; color: #14532d; }
    .psych-style { background-color: #f5f3ff; border-color: #8b5cf6; color: #4c1d95; }
    .street-style { background-color: #fff1f2; border-color: #f43f5e; color: #9f1239; }

    /* بطاقات النتائج الرسمية العريضة */
    .finding-card {
        background: white; padding: 20px; border-radius: 12px;
        margin-bottom: 15px; border-right: 6px solid #cbd5e1;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        display: block !important;
        width: 100% !important;
        word-break: keep-all !important;
    }
    
    input[type="password"] { direction: ltr !important; text-align: left !important; }
    .stButton button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background-color: #1e3a8a; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 3. القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.title("🛡️ المحقق الاستراتيجي")
    api_key = st.text_input("مفتاح Gemini السري:", type="password", placeholder="AIza...")
    st.divider()
    v_files = st.file_uploader("قبو الحقائق (Vault):", accept_multiple_files=True, key="vault")
    o_files = st.file_uploader("ملفات الخصم (Opponent):", accept_multiple_files=True, key="opponent")
    if st.button("تصفير الجلسة 🗑️"):
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# --- 4. محرك العقول الثلاثة ---
with st.form("war_room_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف الحالي:", height=100)
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

if (btn_L or btn_P or btn_S) and api_key and user_query:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if btn_L: role, label, style = "مستشار قانوني خبير", "⚖️ القانوني", "legal-style"
        elif btn_P: role, label, style = "محلل نفسي جنائي", "🧠 النفسي", "psych-style"
        else: role, label, style = "مفاوض استراتيجي داهية", "🧨 الداهية", "street-style"

        def read_docs(files):
            text = ""
            for f in files:
                if f.type == "application/pdf":
                    with fitz.open(stream=f.read(), filetype="pdf") as doc:
                        for page in doc: text += page.get_text() + "\n"
            return text

        v_context = read_docs(v_files if v_files else [])
        o_context = read_docs(o_files if o_files else [])

        prompt = f"تقمص دور {role}. الحقائق: {v_context[:10000]}. الخصم: {o_context[:10000]}. السؤال: {user_query}"
        
        with st.spinner("جاري التحليل..."):
            response = model.generate_content(prompt)
            st.session_state.chat_history.append({"label": label, "content": response.text, "style": style})
            st.rerun()
    except Exception as e:
        st.error(f"خطأ: {e}")

# --- 5. عرض المحادثة (الآن بقوة HTML لمنع التكدس) ---
for chat in st.session_state.chat_history:
    st.write(f'''
        <div class="msg-box {chat['style']}">
            <b>{chat['label']}:</b><br>
            {chat['content']}
        </div>
    ''', unsafe_allow_html=True)

# --- 6. قسم النتائج الرسمية ---
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    st.write(f'''
        <div class="finding-card" style="border-right-color: #1e3a8a;">
            <b style="color: #1e3a8a;">⚖️ الثغرات المستخرجة:</b><br>
            سيتم عرض التناقضات المادية هنا بشكل أفقي سليم.
        </div>
        <div class="finding-card" style="border-right-color: #8b5cf6;">
            <b style="color: #8b5cf6;">🧠 نمط الخصم:</b><br>
            تحليل دوافع الخصم بناءً على الأدلة.
        </div>
    ''', unsafe_allow_html=True)
