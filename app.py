import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io

# --- 1. الإعدادات الحاسمة لمنع الانهيار الأفقي ---
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* فرض العرض الأفقي ومنع تكسر الحروف نهائياً */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* إلغاء أي تأثير للأعمدة الضيقة التي تسبب مشكلة (م-ف-ت-ا-ح) */
    .stMarkdown p, .stMarkdown div {
        display: block !important;
        white-space: pre-wrap !important; /* يحافظ على الكلمات أفقية */
        word-break: keep-all !important; /* يمنع تحويل الكلمات إلى حروف عمودية */
        overflow-wrap: normal !important;
        min-width: 320px !important; /* ضمان مساحة كافية للكلمات العربية */
    }

    /* تنسيق فقاعات المحادثة بشكل مستقل تماماً عن Streamlit */
    .msg-box { 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 20px; 
        line-height: 1.8; 
        border-right: 12px solid; 
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        width: 100% !important;
        background-color: #ffffff;
        display: inline-block !important; /* يمنع التكدس الرأسي */
    }

    .user-style { border-color: #1e3a8a; background-color: #f8fafc; color: #1e3a8a; }
    .ai-style { border-color: #10b981; background-color: #f0fdf4; color: #14532d; }
    
    /* بطاقات النتائج الرسمية العريضة جداً */
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
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 3. القائمة الجانبية (The Secure Vault) ---
with st.sidebar:
    st.title("🛡️ المحقق الاستراتيجي")
    api_key = st.text_input("مفتاح Gemini السري:", type="password", placeholder="AIza...")
    st.divider()
    v_files = st.file_uploader("قبو الحقائق (Vault):", accept_multiple_files=True)
    o_files = st.file_uploader("ملفات الخصم (Opponent):", accept_multiple_files=True)
    if st.button("تفريغ الذاكرة 🗑️"):
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# --- 4. المحرك الاستراتيجي ---
with st.form("war_room_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف الحالي هنا:", height=100)
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

if (btn_L or btn_P or btn_S) and api_key and user_query:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # اختيار الهوية
        label, style = ("⚖️ القانوني", "ai-style") if btn_L else (("🧠 النفسي", "ai-style") if btn_P else ("🧨 الداهية", "ai-style"))
        
        # استخلاص النصوص من المستندات
        def get_text(files):
            text = ""
            for f in files:
                if f.type == "application/pdf":
                    with fitz.open(stream=f.read(), filetype="pdf") as doc:
                        for page in doc: text += page.get_text()
            return text

        v_context = get_text(v_files if v_files else [])
        o_context = get_text(o_files if o_files else [])

        prompt = f"حلل بذكاء: الحقائق: {v_context[:8000]}. الخصم: {o_context[:8000]}. السؤال: {user_query}"
        
        with st.spinner("جاري استنتاج الحجج..."):
            response = model.generate_content(prompt)
            st.session_state.chat_history.append({"q": user_query, "a": response.text, "label": label, "style": style})
            st.rerun()
    except Exception as e:
        st.error(f"حدث خطأ: {e}")

# --- 5. عرض المحادثة (الآن بفرض HTML العريض) ---
for chat in st.session_state.chat_history:
    # عرض سؤال المستخدم
    st.markdown(f'<div class="msg-box user-style"><b>👤 أنت:</b><br>{chat["q"]}</div>', unsafe_allow_html=True)
    # عرض رد المستشار
    st.markdown(f'<div class="msg-box ai-style"><b>{chat["label"]}:</b><br>{chat["a"]}</div>', unsafe_allow_html=True)

# --- 6. قسم النتائج الرسمية ---
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    st.markdown(f'''
        <div class="finding-card">
            <b style="color: #1e3a8a;">⚖️ الثغرات المستخرجة:</b><br>
            تم تحليل البيانات وستظهر النتائج هنا بشكل أفقي سليم تماماً.
        </div>
        <div class="finding-card" style="border-right-color: #8b5cf6;">
            <b style="color: #8b5cf6;">🧠 نمط الخصم:</b><br>
            تحليل التناقضات السلوكية في الملفات المرفوعة.
        </div>
    ''', unsafe_allow_html=True)
